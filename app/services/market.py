"""Fetch market data: VIX, SPY options volume, Put/Call ratio."""
import logging
from datetime import date, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

# Module-level error tracker - cleared at start of each screening
last_errors: dict[str, str] = {}


def reset_errors():
    last_errors.clear()


def fetch_vix() -> float | None:
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="5d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
        last_errors["vix"] = "empty history"
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        logger.error(f"VIX fetch failed: {msg}")
        last_errors["vix"] = msg
    return None


def fetch_spy_options_volume() -> tuple[int | None, int | None]:
    """Returns (today_volume, 20d_avg_volume)."""
    try:
        ticker = yf.Ticker("SPY")
        hist = ticker.history(period="25d")
        if len(hist) >= 2:
            today_vol = int(hist["Volume"].iloc[-1])
            avg_vol = int(hist["Volume"].iloc[-21:-1].mean()) if len(hist) >= 21 else int(hist["Volume"].mean())
            return today_vol, avg_vol
        last_errors["spy_vol"] = f"only {len(hist)} rows"
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        logger.error(f"SPY volume fetch failed: {msg}")
        last_errors["spy_vol"] = msg
    return None, None


def fetch_put_call_ratio() -> float | None:
    """Estimate put/call ratio from SPY options chain."""
    try:
        ticker = yf.Ticker("SPY")
        expirations = ticker.options
        if not expirations:
            last_errors["pcr"] = "no expirations"
            return None
        chain = ticker.option_chain(expirations[0])
        put_vol = chain.puts["volume"].sum()
        call_vol = chain.calls["volume"].sum()
        if call_vol > 0:
            return round(float(put_vol / call_vol), 3)
        last_errors["pcr"] = "call_vol is 0"
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        logger.error(f"Put/Call ratio fetch failed: {msg}")
        last_errors["pcr"] = msg
    return None
