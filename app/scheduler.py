"""APScheduler configuration for screening at NYSE open/close."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.screener import run_daily_screening

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    # NYSE Open: 9:30 EST = UTC 13:30
    scheduler.add_job(
        run_daily_screening,
        trigger="cron",
        hour=13, minute=30,
        kwargs={"screening_type": "open"},
        id="screening_nyse_open",
        replace_existing=True,
    )
    # NYSE Close: 16:00 EST = UTC 20:00
    scheduler.add_job(
        run_daily_screening,
        trigger="cron",
        hour=20, minute=0,
        kwargs={"screening_type": "close"},
        id="screening_nyse_close",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: screening at UTC 13:30 (NYSE open) and UTC 20:00 (NYSE close)")


def stop_scheduler():
    scheduler.shutdown(wait=False)
