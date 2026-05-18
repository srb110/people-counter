"""
scheduler.py — Automatic batch processing scheduler.
Runs batch processing automatically at set intervals.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import os

log = logging.getLogger("scheduler")

def create_scheduler(process_batch_func):
    """
    Build and return the scheduler.
    server.py calls this once on startup.
    """
    scheduler = BackgroundScheduler(timezone="Europe/Paris")

    # Run batch every 30 minutes
    interval_minutes = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))

    scheduler.add_job(
        process_batch_func,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="batch_interval",
        name=f"Batch every {interval_minutes} min",
        replace_existing=True,
        misfire_grace_time=60,
    )

    log.info(f"Scheduler: runs every {interval_minutes} minutes")
    return scheduler
