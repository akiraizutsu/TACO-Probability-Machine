from datetime import date, datetime
from sqlalchemy import String, Integer, Float, BigInteger, Text, Boolean, Date, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    type_label: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    signals: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_candidate: Mapped[bool] = mapped_column(Boolean, default=False)


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True)
    vix: Mapped[float | None] = mapped_column(Float, nullable=True)
    put_call_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    spy_volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    spy_volume_avg: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    volume_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    polymarket_new_accounts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    taco_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ScreeningLog(Base):
    __tablename__ = "screening_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="success")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_candidates: Mapped[int] = mapped_column(Integer, default=0)


class ScoreHistory(Base):
    """Append-only log of every TACO score calculation.

    One row per screening run (2x/day + manual). Used for the time-series chart.
    """
    __tablename__ = "score_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    score: Mapped[int] = mapped_column(Integer)
    vix: Mapped[float | None] = mapped_column(Float, nullable=True)
    put_call_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    option_volume_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    polymarket_anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    screening_type: Mapped[str] = mapped_column(String(20), default="manual")  # open / close / manual
