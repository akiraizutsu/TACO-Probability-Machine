"""Check Polymarket for unusual activity on political markets."""
import logging
import httpx

logger = logging.getLogger(__name__)

POLYMARKET_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"


async def fetch_political_markets() -> list[dict]:
    """Fetch active political/geopolitical markets from Polymarket."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{GAMMA_API}/markets",
                params={"closed": "false", "tag": "Politics", "limit": 20, "order": "volume24hr", "ascending": "false"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"Polymarket fetch failed: {e}")
    return []


def estimate_new_accounts(markets: list[dict]) -> int:
    """Rough estimate of new account activity from market data.

    This is an approximation based on volume spikes -
    actual new wallet detection would require on-chain analysis.
    """
    count = 0
    for market in markets:
        vol_24h = float(market.get("volume24hr", 0) or 0)
        vol_total = float(market.get("volume", 1) or 1)
        if vol_total > 0 and vol_24h / vol_total > 0.3:
            count += int(vol_24h / 1000)
    return count


def detect_anomalies(markets: list[dict]) -> list[dict]:
    """Detect unusual activity patterns in political markets."""
    anomalies = []
    for market in markets:
        vol_24h = float(market.get("volume24hr", 0) or 0)
        vol_total = float(market.get("volume", 1) or 1)
        ratio = vol_24h / vol_total if vol_total > 0 else 0
        if ratio > 0.2 and vol_24h > 50000:
            anomalies.append({
                "market": market.get("question", "Unknown"),
                "volume_24h": vol_24h,
                "volume_ratio": round(ratio, 3),
                "slug": market.get("slug", ""),
            })
    return anomalies
