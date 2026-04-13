"""Fetch market data: VIX, SPY options volume, Put/Call ratio."""
import logging
from datetime import date, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_vix() -> float | None:
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception as e:
        logger.error(f"VIX fetch failed: {e}")
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
    except Exception as e:
        logger.error(f"SPY volume fetch failed: {e}")
    return None, None


def fetch_put_call_ratio() -> float | None:
    """Estimate put/call ratio from SPY options chain."""
    try:
        ticker = yf.Ticker("SPY")
        expirations = ticker.options
        if not expirations:
            return None
        chain = ticker.option_chain(expirations[0])
        put_vol = chain.puts["volume"].sum()
        call_vol = chain.calls["volume"].sum()
        if call_vol > 0:
            return round(float(put_vol / call_vol), 3)
    except Exception as e:
        logger.error(f"Put/Call ratio fetch failed: {e}")
    return None
