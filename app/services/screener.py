"""Daily screening: fetch market data, check Polymarket, calculate TACO score.

TACO score philosophy (v2):
--------------------------
The score detects the "calm before the storm" pattern — when market
volatility has subsided AND unusual positioning persists.

A high score means: "despite apparent calm, someone is positioning for chaos."
A low score means: "nothing unusual, no reason to worry."

This is the opposite of a simple volatility gauge. We want to flag
the moment *after* a storm has passed — when the system looks calm but
inside players may already know the next move.

Components:
  1. Calm-before-storm (0-40): how much has VIX dropped from recent peak
  2. Unusual-in-calm (0-40): options volume surge when VIX is low
                              (negative contribution if VIX is in panic mode)
  3. Polymarket spike (0-20): sudden burst above baseline
  4. PCR extreme (+10): sub-signal for unusual put/call positioning
"""
import asyncio
import logging
from datetime import date, datetime, timedelta
from sqlalchemy import desc
from app.database import SessionLocal
from app.models import MarketData, ScreeningLog, ScoreHistory
from app.services.market import fetch_vix, fetch_spy_options_volume, fetch_put_call_ratio, reset_errors, last_errors
from app.services.polymarket import fetch_political_markets, estimate_new_accounts, detect_anomalies

logger = logging.getLogger(__name__)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def calc_taco_score(
    vix: float | None,
    pcr: float | None,
    vol_ratio: float | None,
    poly_accounts: int | None,
    recent_max_vix: float | None = None,
    poly_baseline: int | None = None,
) -> tuple[int, dict]:
    """Return (score, breakdown) where breakdown exposes each signal.

    recent_max_vix: max VIX over the last ~7 days (excludes today).
    poly_baseline: median poly_accounts over the last ~7 days (excludes today).
    """
    breakdown = {
        "calm_before_storm": 0.0,
        "unusual_in_calm": 0.0,
        "polymarket_spike": 0.0,
        "pcr_extreme": 0.0,
    }

    # ---- Signal 1: Calm before storm (0-40) --------------------------------
    # The VIX has dropped from its recent peak. The bigger the drop, the more
    # suspicious the current calm feels.
    if recent_max_vix is not None and vix is not None:
        drop = float(recent_max_vix) - float(vix)
        if drop > 0:
            breakdown["calm_before_storm"] = clamp(drop * 5.0, 0, 40)

    # ---- Signal 2: Unusual activity in calm market (-15 to +40) -----------
    # The most important signal: VIX < 20 AND options volume > 2x normal
    # means "positioning for something while the crowd is relaxed."
    if vix is not None and vol_ratio is not None:
        v = float(vix)
        vr = float(vol_ratio)
        if v < 20:
            # Calm market → amplify signal
            if vr > 1:
                breakdown["unusual_in_calm"] = clamp((vr - 1) * 20.0, 0, 40)
        elif v < 25:
            # Transitional → moderate signal
            if vr > 1:
                breakdown["unusual_in_calm"] = clamp((vr - 1) * 8.0, 0, 20)
        else:
            # Panic market (VIX ≥ 25) → options volume is just hedging, not inside info
            # Slightly *reduce* the score because this is expected behavior.
            if vr > 1.5:
                breakdown["unusual_in_calm"] = -clamp((vr - 1) * 4.0, 0, 15)

    # ---- Signal 3: Polymarket spike (0-20) ---------------------------------
    # Only flag when activity is meaningfully above recent baseline.
    if poly_accounts is not None and poly_baseline and poly_baseline > 0:
        ratio = float(poly_accounts) / float(poly_baseline)
        if ratio > 1.2:
            breakdown["polymarket_spike"] = clamp((ratio - 1.0) * 30.0, 0, 20)
    elif poly_accounts is not None and poly_baseline is None:
        # Cold start: no baseline yet. Use a reasonable absolute floor
        # so early runs don't max out the gauge on normal traffic.
        if poly_accounts > 40000:
            breakdown["polymarket_spike"] = clamp((poly_accounts - 40000) / 2000.0, 0, 20)

    # ---- Sub-signal: PCR extreme (+10) -------------------------------------
    if pcr is not None:
        p = float(pcr)
        if p > 1.8 or p < 0.5:
            breakdown["pcr_extreme"] = 10.0

    total = sum(breakdown.values())
    final = round(clamp(total, 0, 100))
    return final, breakdown


def _recent_max_vix(db, today: date, days: int = 7) -> float | None:
    """Max VIX from score_history over the last N days (excluding today)."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(ScoreHistory.vix)
        .filter(ScoreHistory.timestamp >= cutoff, ScoreHistory.vix.isnot(None))
        .all()
    )
    vals = [r[0] for r in rows if r[0] is not None]
    return max(vals) if vals else None


def _poly_baseline(db, days: int = 7) -> int | None:
    """Median-ish baseline (simple average) of polymarket activity over last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(MarketData.polymarket_new_accounts)
        .filter(MarketData.date >= cutoff.date(), MarketData.polymarket_new_accounts.isnot(None))
        .all()
    )
    vals = [r[0] for r in rows if r[0] and r[0] > 0]
    if not vals:
        return None
    return int(sum(vals) / len(vals))


def run_daily_screening(screening_type: str = "manual"):
    """Main screening entry point, called by scheduler.

    screening_type: 'open' (NYSE open), 'close' (NYSE close), or 'manual'
    """
    logger.info(f"Starting screening (type={screening_type})...")
    db = SessionLocal()
    try:
        today = date.today()
        reset_errors()

        # ---- 1. Market data ------------------------------------------------
        # Historical avg SPY volume from our own DB (last 20 days, excluding today)
        spy_history = (
            db.query(MarketData.spy_volume)
            .filter(MarketData.date < today, MarketData.spy_volume.isnot(None))
            .order_by(desc(MarketData.date))
            .limit(20)
            .all()
        )
        hist_vols = [v[0] for v in spy_history if v[0] and v[0] > 0]
        historical_avg = int(sum(hist_vols) / len(hist_vols)) if hist_vols else None

        vix = fetch_vix()
        spy_vol, spy_avg = fetch_spy_options_volume(historical_avg=historical_avg)
        pcr = fetch_put_call_ratio()
        vol_ratio = round(spy_vol / spy_avg, 2) if spy_vol and spy_avg and spy_avg > 0 else None

        # ---- 2. Polymarket -------------------------------------------------
        markets = asyncio.run(fetch_political_markets())
        poly_accounts = estimate_new_accounts(markets)
        anomalies = detect_anomalies(markets)

        # ---- 3. Historical context for new scoring logic -------------------
        recent_max_vix = _recent_max_vix(db, today)
        poly_baseline = _poly_baseline(db)

        # ---- 4. TACO score -------------------------------------------------
        score, breakdown = calc_taco_score(
            vix=vix,
            pcr=pcr,
            vol_ratio=vol_ratio,
            poly_accounts=poly_accounts,
            recent_max_vix=recent_max_vix,
            poly_baseline=poly_baseline,
        )

        # ---- 5. Save market data ------------------------------------------
        raw = {
            "anomalies": anomalies,
            "breakdown": breakdown,
            "recent_max_vix": recent_max_vix,
            "poly_baseline": poly_baseline,
        }
        existing = db.query(MarketData).filter(MarketData.date == today).first()
        if existing:
            existing.vix = vix
            existing.put_call_ratio = pcr
            existing.spy_volume = spy_vol
            existing.spy_volume_avg = spy_avg
            existing.volume_ratio = vol_ratio
            existing.polymarket_new_accounts = poly_accounts
            existing.taco_score = score
            existing.raw_data = raw
        else:
            db.add(MarketData(
                date=today, vix=vix, put_call_ratio=pcr,
                spy_volume=spy_vol, spy_volume_avg=spy_avg,
                volume_ratio=vol_ratio, polymarket_new_accounts=poly_accounts,
                taco_score=score, raw_data=raw,
            ))

        # ---- 6. Score history (one row per run) ---------------------------
        poly_anomaly_score = breakdown["polymarket_spike"]
        db.add(ScoreHistory(
            timestamp=datetime.utcnow(),
            score=score,
            vix=vix,
            put_call_ratio=pcr,
            option_volume_ratio=vol_ratio,
            polymarket_anomaly_score=poly_anomaly_score,
            screening_type=screening_type,
        ))

        # ---- 7. Screening log ---------------------------------------------
        err_str = " | errors: " + "; ".join(f"{k}={v}" for k, v in last_errors.items()) if last_errors else ""
        bd_str = ", ".join(f"{k}={round(v, 1)}" for k, v in breakdown.items())
        summary = (
            f"[{screening_type}] VIX={vix} (max7d={recent_max_vix}), PCR={pcr}, "
            f"VolRatio={vol_ratio}, PolyAccts={poly_accounts} (base={poly_baseline}), "
            f"Score={score} [{bd_str}]{err_str}"
        )
        db.add(ScreeningLog(
            run_at=datetime.utcnow(), status="success",
            summary=summary, new_candidates=len(anomalies),
        ))
        db.commit()
        logger.info(f"Screening complete: {summary}")

    except Exception as e:
        logger.error(f"Screening failed: {e}", exc_info=True)
        db.rollback()
        db.add(ScreeningLog(run_at=datetime.utcnow(), status="error", summary=str(e), new_candidates=0))
        db.commit()
    finally:
        db.close()
