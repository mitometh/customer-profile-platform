"""Scheduler entry point. Runs periodic jobs for metric recomputation.

Usage: python -m scheduler.runner

Jobs:
    - metric_recompute: Recompute support_tickets_last_30d
    - health_score: Composite health score 0-100
    - days_since_contact: now - max(occurred_at)

Interval is controlled by SCHEDULER_INTERVAL_MINUTES env var (default: 1).
"""

import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.infrastructure.logging import configure_logging, get_logger


async def main() -> None:
    """Configure and start the scheduler with all periodic jobs."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
    logger = get_logger("scheduler")

    interval = settings.SCHEDULER_INTERVAL_MINUTES

    scheduler = AsyncIOScheduler()

    # Import jobs
    from app.application.jobs.days_since_contact import run_days_since_contact
    from app.application.jobs.health_score import run_health_score
    from app.application.jobs.metric_recompute import run_metric_recompute

    trigger = IntervalTrigger(minutes=interval)

    scheduler.add_job(
        run_metric_recompute,
        trigger,
        id="metric_recompute",
        name="Recompute support_tickets_last_30d",
    )
    scheduler.add_job(
        run_health_score,
        trigger,
        id="health_score",
        name="Compute composite health score",
    )
    scheduler.add_job(
        run_days_since_contact,
        trigger,
        id="days_since_contact",
        name="Compute days since last contact",
    )

    scheduler.start()
    logger.info(
        "Scheduler started — all jobs run every %d minute(s)",
        interval,
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
