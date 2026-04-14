"""Daily screening: fetch market data, check Polymarket, calculate TACO score."""
import asyncio
import logging
from datetime import date, datetime
from sqlalchemy import desc
from app.database import SessionLocal
from app.models import MarketData, ScreeningLog
from app.services.market import fetch_vix, fetch_spy_options_volume, fetch_put_call_ratio, reset_errors, last_errors
from app.services.polymarket import fetch_political_markets, estimate_new_accounts, detect_anomalies

logger = logging.getLogger(__name__)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def calc_taco_score(vix: float | None, pcr: float | None, vol_ratio: float | None, poly_accounts: int | None) -> int:
    """Same weighted average as the frontend simulator."""
    vix_norm = clamp((float(vix or 12) - 12) / (80 - 12) * 100, 0, 100)
    pcr_norm = clamp((float(pcr or 0.5) - 0.5) / (2.0 - 0.5) * 100, 0, 100)
    vol_norm = clamp((float(vol_ratio or 1) - 1) / (50 - 1) * 100, 0, 100)
    poly_norm = clamp(float(poly_accounts or 0) / 500 * 100, 0, 100)
    return round(clamp(vix_norm * 0.25 + pcr_norm * 0.20 + vol_norm * 0.35 + poly_norm * 0.20, 0, 100))


def run_daily_screening():
    """Main screening entry point, called by scheduler."""
    logger.info("Starting daily screening...")
    db = SessionLocal()
    try:
        today = date.today()
        reset_errors()

        # 1. Market data
        # Historical avg from our own DB (last 20 days, excluding today)
        history = (
            db.query(MarketData.spy_volume)
            .filter(MarketData.date < today, MarketData.spy_volume.isnot(None))
            .order_by(desc(MarketData.date))
            .limit(20)
            .all()
        )
        hist_vols = [v[0] for v in history if v[0] and v[0] > 0]
        historical_avg = int(sum(hist_vols) / len(hist_vols)) if hist_vols else None

        vix = fetch_vix()
        spy_vol, spy_avg = fetch_spy_options_volume(historical_avg=historical_avg)
        pcr = fetch_put_call_ratio()
        vol_ratio = round(spy_vol / spy_avg, 2) if spy_vol and spy_avg and spy_avg > 0 else None

        # 2. Polymarket
        markets = asyncio.run(fetch_political_markets())
        poly_accounts = estimate_new_accounts(markets)
        anomalies = detect_anomalies(markets)

        # 3. TACO score
        score = calc_taco_score(vix, pcr, vol_ratio, poly_accounts)

        # 4. Save market data
        existing = db.query(MarketData).filter(MarketData.date == today).first()
        if existing:
            existing.vix = vix
            existing.put_call_ratio = pcr
            existing.spy_volume = spy_vol
            existing.spy_volume_avg = spy_avg
            existing.volume_ratio = vol_ratio
            existing.polymarket_new_accounts = poly_accounts
            existing.taco_score = score
            existing.raw_data = {"anomalies": anomalies}
        else:
            db.add(MarketData(
                date=today, vix=vix, put_call_ratio=pcr,
                spy_volume=spy_vol, spy_volume_avg=spy_avg,
                volume_ratio=vol_ratio, polymarket_new_accounts=poly_accounts,
                taco_score=score, raw_data={"anomalies": anomalies},
            ))

        # 5. Log
        err_str = " | errors: " + "; ".join(f"{k}={v}" for k, v in last_errors.items()) if last_errors else ""
        summary = f"VIX={vix}, PCR={pcr}, VolRatio={vol_ratio}, PolyAccts={poly_accounts}, Score={score}, Anomalies={len(anomalies)}{err_str}"
        db.add(ScreeningLog(
            run_at=datetime.utcnow(), status="success",
            summary=summary, new_candidates=len(anomalies),
        ))
        db.commit()
        logger.info(f"Screening complete: {summary}")

    except Exception as e:
        logger.error(f"Screening failed: {e}")
        db.add(ScreeningLog(run_at=datetime.utcnow(), status="error", summary=str(e), new_candidates=0))
        db.commit()
    finally:
        db.close()
