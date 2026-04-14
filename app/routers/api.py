from datetime import date, datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, MarketData, ScreeningLog
from app.schemas import EventCreate, EventUpdate
from app.auth import require_admin

router = APIRouter(prefix="/api")


def _event_to_dict(e: Event) -> dict:
    return {
        "id": e.id,
        "date": e.date.strftime("%Y.%m.%d"),
        "date_iso": e.date.isoformat(),
        "name": e.name,
        "type": e.type,
        "typeLabel": e.type_label,
        "summary": e.summary,
        "score": e.score,
        "signals": e.signals,
        "is_candidate": e.is_candidate,
    }


@router.get("/events")
def list_events(type: str | None = None, include_candidates: bool = False, db: Session = Depends(get_db)):
    q = db.query(Event)
    if not include_candidates:
        q = q.filter(Event.is_candidate == False)
    if type:
        q = q.filter(Event.type == type)
    events = q.order_by(desc(Event.score)).all()
    return [_event_to_dict(e) for e in events]


@router.get("/events/candidates")
def list_candidates(db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.is_candidate == True).order_by(desc(Event.created_at)).all()
    return [_event_to_dict(e) for e in events]


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    e = db.get(Event, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_dict(e)


@router.post("/events", status_code=201)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    _user: str = Depends(require_admin),
):
    if db.get(Event, payload.id):
        raise HTTPException(status_code=409, detail=f"Event with id '{payload.id}' already exists")
    event = Event(
        id=payload.id,
        date=payload.date,
        name=payload.name,
        type=payload.type,
        type_label=payload.type_label,
        summary=payload.summary,
        score=payload.score,
        signals=[s.model_dump() for s in payload.signals],
        is_candidate=payload.is_candidate,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_to_dict(event)


@router.put("/events/{event_id}")
def update_event(
    event_id: str,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    _user: str = Depends(require_admin),
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    if "signals" in data and data["signals"] is not None:
        data["signals"] = [s if isinstance(s, dict) else s.model_dump() for s in data["signals"]]
    if "type_label" in data:
        event.type_label = data.pop("type_label")
    for key, value in data.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return _event_to_dict(event)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    _user: str = Depends(require_admin),
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return None


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
