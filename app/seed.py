"""Seed the database with initial TACO events."""
from datetime import date
from sqlalchemy.orm import Session
from app.models import Event


SEED_EVENTS = [
    Event(
        id="tariff-pause-2025", date=date(2025, 4, 9),
        name="関税90日間一時停止", type="tariff", type_label="関税",
        summary='トランプが"A GREAT TIME TO BUY!!!"と投稿した4時間後に関税90日間一時停止を発表。SPYコールオプション$2.1M分が数時間で$30M超に。',
        score=95,
        signals=[
            {"label": "事前シグナル", "val": "18分前", "cls": "red"},
            {"label": "SPY 0DTEコール", "val": "5,105枚", "cls": "red"},
            {"label": "エントリー → ピーク", "val": "$4.20 → $42", "cls": "red"},
            {"label": "リターン", "val": "+900%", "cls": "red"},
            {"label": "推定利益", "val": "$30M+", "cls": "red"},
            {"label": "空売り構築期間", "val": "3/31〜4/4", "cls": "amber"},
            {"label": "Truth Social投稿", "val": '"BE COOL" + "BUY!!!"', "cls": "amber"},
            {"label": "当日出来高", "val": "8,500万枚（過去最高）", "cls": "amber"},
        ],
    ),
    Event(
        id="china-rare-earth-2025", date=date(2025, 10, 10),
        name="対中100%関税（レアアース報復）", type="tariff", type_label="関税",
        summary="単一のクジラがHyperliquidでBTC/ETHの9桁ショートを発表30分前に構築。推定利益$160M。",
        score=88,
        signals=[
            {"label": "事前シグナル", "val": "30分前", "cls": "red"},
            {"label": "対象商品", "val": "BTC + ETH ショート", "cls": "red"},
            {"label": "ポジション規模", "val": "9桁（億ドル超）", "cls": "red"},
            {"label": "推定利益", "val": "$160M", "cls": "red"},
            {"label": "強制清算額", "val": "$19.3B / 24時間", "cls": "amber"},
            {"label": "プラットフォーム", "val": "Hyperliquid", "cls": "amber"},
        ],
    ),
    Event(
        id="venezuela-2026", date=date(2026, 1, 3),
        name="ベネズエラ — マドゥロ拘束", type="geopolitical", type_label="地政学",
        summary="Polymarket上の匿名ユーザーがマドゥロ失脚に賭けて$400Kの利益。カラカス軍事作戦の数時間前。",
        score=82,
        signals=[
            {"label": "事前シグナル", "val": "数時間前", "cls": "amber"},
            {"label": "プラットフォーム", "val": "Polymarket", "cls": "amber"},
            {"label": "推定利益", "val": "$400K", "cls": "red"},
            {"label": "パターン", "val": "単一匿名アカウント", "cls": "amber"},
        ],
    ),
    Event(
        id="iran-strikes-2026", date=date(2026, 2, 28),
        name="イラン攻撃開始", type="military", type_label="軍事",
        summary="Polymarket上の38アカウント（単一人物と推定）が米・イスラエルによる攻撃タイミングに的中。暗号資産での準備は6日前から。",
        score=91,
        signals=[
            {"label": "準備期間", "val": "6日間", "cls": "red"},
            {"label": "賭け実行", "val": "攻撃の数時間前", "cls": "red"},
            {"label": "アカウント数", "val": "38（同一人物と推定）", "cls": "red"},
            {"label": "暗号資産送金開始", "val": "2月22日", "cls": "red"},
            {"label": "推定利益", "val": "$2M+", "cls": "red"},
            {"label": "プラットフォーム", "val": "Polymarket", "cls": "amber"},
        ],
    ),
    Event(
        id="iran-pause-2026", date=date(2026, 3, 23),
        name="イランエネルギー施設攻撃延期", type="military", type_label="軍事",
        summary="Truth Social投稿の15分前に、2分間で$760Mの原油先物が取引。同時間帯の通常出来高は70万バレル。",
        score=97,
        signals=[
            {"label": "事前シグナル", "val": "15分前", "cls": "red"},
            {"label": "原油先物出来高", "val": "$760M / 2分間", "cls": "red"},
            {"label": "Brentロット数", "val": "6,200 / 1分間", "cls": "red"},
            {"label": "通常出来高", "val": "70万バレル", "cls": "green"},
            {"label": "Brent価格変動", "val": "$112 → $99（-12%）", "cls": "red"},
            {"label": "WTI価格変動", "val": "$99 → $86（-13%）", "cls": "red"},
            {"label": "S&P先物", "val": "同時にスパイク", "cls": "amber"},
            {"label": "投稿時刻", "val": "Truth Social 7:04am", "cls": "amber"},
        ],
    ),
    Event(
        id="iran-ceasefire-2026", date=date(2026, 4, 7),
        name="米イラン停戦発表", type="military", type_label="軍事",
        summary="トランプ投稿の数分前に50以上の新規Polymarketアカウントが初めての賭けを実行。投稿12分前に作成されたアカウントが$48.5Kの利益。",
        score=96,
        signals=[
            {"label": "事前シグナル", "val": "数分前", "cls": "red"},
            {"label": "新規アカウント", "val": "50+（全て初回ベット）", "cls": "red"},
            {"label": "最大利益", "val": "$72K → $200K", "cls": "red"},
            {"label": "原油先物", "val": "〜$950M", "cls": "red"},
            {"label": "12分前作成ウォレット", "val": "$31.9K → $48.5K", "cls": "red"},
            {"label": "最高的中率", "val": "93%", "cls": "red"},
            {"label": "トランプの前フリ", "val": '"文明が滅びる"', "cls": "amber"},
            {"label": "コントラクト状態", "val": "係争中", "cls": "amber"},
        ],
    ),
]


def seed_events(db: Session):
    for event in SEED_EVENTS:
        existing = db.get(Event, event.id)
        if not existing:
            db.add(event)
    db.commit()
