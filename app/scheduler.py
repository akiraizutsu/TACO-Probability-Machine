"""APScheduler configuration for daily screening."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.screener import run_daily_screening

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_daily_screening,
        trigger="cron",
        hour=14, minute=0,  # UTC 14:00 = EST 9:00 / JST 23:00
        id="daily_screening",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: daily screening at UTC 14:00")


def stop_scheduler():
    scheduler.shutdown(wait=False)
