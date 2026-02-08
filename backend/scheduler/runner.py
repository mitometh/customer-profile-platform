"""Scheduler entry point. Runs daily cron jobs for metric recomputation.

Usage: python -m scheduler.runner

Jobs:
    - metric_recompute: Recompute support_tickets_last_30d (02:00 UTC)
    - health_score: Composite health score 0-100 (02:15 UTC)
    - days_since_contact: now - max(occurred_at) (02:30 UTC)
"""

import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.infrastructure.logging import configure_logging, get_logger


async def main() -> None:
    """Configure and start the scheduler with all daily jobs."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
    logger = get_logger("scheduler")

    scheduler = AsyncIOScheduler()

    # Import jobs
    from app.application.jobs.days_since_contact import run_days_since_contact
    from app.application.jobs.health_score import run_health_score
    from app.application.jobs.metric_recompute import run_metric_recompute

    # Schedule daily at 2:00 AM UTC
    scheduler.add_job(
        run_metric_recompute,
        CronTrigger(hour=2, minute=0),
        id="metric_recompute",
        name="Recompute support_tickets_last_30d",
    )
    scheduler.add_job(
        run_health_score,
        CronTrigger(hour=2, minute=15),
        id="health_score",
        name="Compute composite health score",
    )
    scheduler.add_job(
        run_days_since_contact,
        CronTrigger(hour=2, minute=30),
        id="days_since_contact",
        name="Compute days since last contact",
    )

    scheduler.start()
    logger.info(
        "Scheduler started with 3 daily jobs",
        jobs=["metric_recompute", "health_score", "days_since_contact"],
    )

    # Graceful shutdown handling
    shutdown_event = asyncio.Event()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Received shutdown signal", signal=sig)
        shutdown_event.set()

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Keep running until shutdown
    await shutdown_event.wait()
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
