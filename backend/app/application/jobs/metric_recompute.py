"""Scheduled job: recompute support_tickets_last_30d for all active customers.

Runs daily at 02:00 UTC via the scheduler. Iterates over every active
(non-deleted) customer, counts their support tickets in the last 30 days,
upserts the ``customer_metrics`` row, and appends a snapshot to
``customer_metric_history``.

Errors are handled per-customer so a single failure does not abort the
entire batch.
"""

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.infrastructure.logging import get_logger
from app.infrastructure.models.customer import CustomerModel
from app.infrastructure.models.event import EventModel
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)

logger = get_logger("job.metric_recompute")


async def run_metric_recompute() -> None:
    """Recompute support_tickets_last_30d for all active customers."""
    logger.info("Starting metric recomputation")
    start = time.monotonic()

    async for session in get_session():
        try:
            await _recompute_all(session)
        except Exception as exc:
            logger.error("Metric recomputation failed", error=str(exc))
        break  # Exit the async generator to ensure session cleanup

    elapsed = time.monotonic() - start
    logger.info("Metric recomputation completed", duration_seconds=round(elapsed, 2))


async def _recompute_all(session: AsyncSession) -> None:
    """Core logic: iterate customers and recompute the metric."""
    # Load metric definition
    metric_def_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_def = await metric_def_repo.get_by_name("support_tickets_last_30d")
    if metric_def is None:
        logger.warning("Metric definition 'support_tickets_last_30d' not found")
        return

    # Load all active customers
    result = await session.execute(select(CustomerModel).where(CustomerModel.deleted_at.is_(None)))
    customers = result.scalars().all()

    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

    processed = 0
    errors = 0

    for customer in customers:
        try:
            # Count support tickets in last 30 days
            count_result = await session.execute(
                select(func.count(EventModel.id)).where(
                    EventModel.customer_id == customer.id,
                    EventModel.event_type == "support_ticket",
                    EventModel.occurred_at >= thirty_days_ago,
                    EventModel.deleted_at.is_(None),
                )
            )
            count = count_result.scalar() or 0
            value = Decimal(count)

            # Upsert customer_metrics
            await metric_repo.upsert(customer.id, metric_def.id, value)

            # Append to history
            await history_repo.append(customer.id, metric_def.id, value)

            processed += 1
        except Exception as exc:
            errors += 1
            logger.error(
                "Failed to recompute metric for customer",
                customer_id=str(customer.id),
                error=str(exc),
            )

    logger.info(
        "Metric recomputation completed",
        metric="support_tickets_last_30d",
        processed=processed,
        errors=errors,
    )
