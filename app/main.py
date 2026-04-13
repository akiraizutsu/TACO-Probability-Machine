import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, SessionLocal, Base
from app.models import Event, MarketData, ScreeningLog
from app.routers import api, pages
from app.scheduler import start_scheduler, stop_scheduler
from app.seed import seed_events

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_events(db)
    finally:
        db.close()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(title="TACO Probability Machine", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(api.router)
app.include_router(pages.router)
