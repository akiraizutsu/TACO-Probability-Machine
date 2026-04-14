"""Fetch market data: VIX, SPY options volume, Put/Call ratio.

Uses CBOE's public delayed quotes API (cdn.cboe.com) as primary source.
- No API key required
- No rate limits (static CDN)
- Works reliably from datacenter IPs (Railway)

Historical volume (for 20-day avg) is calculated from our own market_data table.
For the first days until we accumulate history, we use a default of 80M
(typical SPY daily volume).
"""
import logging
import re
import httpx

logger = logging.getLogger(__name__)

last_errors: dict[str, str] = {}

CBOE_QUOTE = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/{symbol}.json"
CBOE_OPTIONS = "https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"

# VIX uses underscore prefix in CBOE's API (_VIX)
VIX_SYMBOL = "_VIX"
SPY_SYMBOL = "SPY"

DEFAULT_SPY_AVG_VOLUME = 80_000_000  # Typical SPY daily volume, used when no history

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def reset_errors():
    last_errors.clear()


def _cboe_quote(symbol: str) -> dict | None:
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as c:
            r = c.get(CBOE_QUOTE.format(symbol=symbol), headers=HEADERS)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        last_errors[f"{symbol}_quote"] = f"{type(e).__name__}: {str(e)[:150]}"
        logger.warning(f"CBOE quote fetch failed for {symbol}: {e}")
        return None


def _cboe_options(symbol: str) -> dict | None:
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(CBOE_OPTIONS.format(symbol=symbol), headers=HEADERS)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        last_errors[f"{symbol}_options"] = f"{type(e).__name__}: {str(e)[:150]}"
        logger.warning(f"CBOE options fetch failed for {symbol}: {e}")
        return None


def fetch_vix() -> float | None:
    data = _cboe_quote(VIX_SYMBOL)
    if not data:
        return None
    try:
        price = data["data"].get("current_price") or data["data"].get("close")
        if price is not None and price > 0:
            return round(float(price), 2)
        last_errors["vix"] = "no price"
    except (KeyError, ValueError) as e:
        last_errors["vix"] = f"parse: {e}"
    return None


def fetch_spy_today_volume() -> int | None:
    """Fetch today's SPY volume from CBOE."""
    data = _cboe_quote(SPY_SYMBOL)
    if not data:
        return None
    try:
        vol = data["data"].get("volume")
        if vol and vol > 0:
            return int(vol)
        last_errors["spy_vol"] = "zero volume"
    except (KeyError, ValueError) as e:
        last_errors["spy_vol"] = f"parse: {e}"
    return None


def fetch_spy_options_volume(historical_avg: int | None = None) -> tuple[int | None, int | None]:
    """Returns (today_volume, avg_volume).

    historical_avg: average volume calculated from our own DB history.
    If None, falls back to DEFAULT_SPY_AVG_VOLUME.
    """
    today_vol = fetch_spy_today_volume()
    avg_vol = historical_avg if historical_avg and historical_avg > 0 else DEFAULT_SPY_AVG_VOLUME
    return today_vol, avg_vol


def fetch_put_call_ratio() -> float | None:
    """Calculate Put/Call ratio from CBOE SPY options chain.

    Option symbol format: SPY{YYMMDD}{C|P}{strike}
    Example: SPY260413C00500000 = SPY 2026-04-13 Call strike $500
    """
    data = _cboe_options(SPY_SYMBOL)
    if not data:
        return None
    try:
        options = data.get("data", {}).get("options", [])
        if not options:
            last_errors["pcr"] = "no options"
            return None
        put_vol = 0
        call_vol = 0
        pattern = re.compile(r"^[A-Z]+\d{6}([CP])")
        for o in options:
            sym = o.get("option", "")
            v = o.get("volume", 0) or 0
            m = pattern.match(sym)
            if m:
                if m.group(1) == "P":
                    put_vol += v
                else:
                    call_vol += v
        if call_vol > 0:
            return round(put_vol / call_vol, 3)
        last_errors["pcr"] = "call_vol is 0"
    except (KeyError, ValueError) as e:
        last_errors["pcr"] = f"parse: {e}"
    return None
