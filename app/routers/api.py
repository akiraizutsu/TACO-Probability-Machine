from datetime import date
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, MarketData, ScreeningLog

router = APIRouter(prefix="/api")


@router.get("/events")
def list_events(type: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Event).filter(Event.is_candidate == False)
    if type:
        q = q.filter(Event.type == type)
    events = q.order_by(desc(Event.score)).all()
    return [
        {
            "id": e.id, "date": e.date.strftime("%Y.%m.%d"), "name": e.name,
            "type": e.type, "typeLabel": e.type_label, "summary": e.summary,
            "score": e.score, "signals": e.signals,
        }
        for e in events
    ]


@router.get("/events/candidates")
def list_candidates(db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.is_candidate == True).order_by(desc(Event.created_at)).all()
    return [
        {
            "id": e.id, "date": e.date.strftime("%Y.%m.%d"), "name": e.name,
            "type": e.type, "typeLabel": e.type_label, "summary": e.summary,
            "score": e.score, "signals": e.signals,
        }
        for e in events
    ]


@router.get("/market/latest")
def market_latest(db: Session = Depends(get_db)):
    row = db.query(MarketData).order_by(desc(MarketData.date)).first()
    if not row:
        return {"date": None, "taco_score": None, "vix": None, "put_call_ratio": None, "volume_ratio": None, "polymarket_new_accounts": None}
    return {
        "date": row.date.isoformat(),
        "taco_score": row.taco_score,
        "vix": row.vix,
        "put_call_ratio": row.put_call_ratio,
        "volume_ratio": row.volume_ratio,
        "polymarket_new_accounts": row.polymarket_new_accounts,
    }


@router.get("/market/history")
def market_history(days: int = 30, db: Session = Depends(get_db)):
    rows = db.query(MarketData).order_by(desc(MarketData.date)).limit(days).all()
    return [
        {"date": r.date.isoformat(), "taco_score": r.taco_score, "vix": r.vix}
        for r in reversed(rows)
    ]


@router.post("/screening/run")
def run_screening(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from app.services.screener import run_daily_screening
    background_tasks.add_task(run_daily_screening)
    return {"status": "started"}


@router.get("/screening/logs")
def screening_logs(limit: int = 10, db: Session = Depends(get_db)):
    rows = db.query(ScreeningLog).order_by(desc(ScreeningLog.run_at)).limit(limit).all()
    return [
        {
            "run_at": r.run_at.isoformat(),
            "status": r.status,
            "summary": r.summary,
            "new_candidates": r.new_candidates,
        }
        for r in rows
    ]
