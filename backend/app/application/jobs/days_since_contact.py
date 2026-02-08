"""Scheduled job: compute days_since_last_contact for all active customers.

Runs daily at 02:30 UTC via the scheduler.

Formula:
    days_since_last_contact = (now - max(occurred_at)).days
    If no events exist for the customer, set to 9999.

Errors are handled per-customer so a single failure does not abort the
entire batch.
"""

import time
from datetime import UTC, datetime
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

logger = get_logger("job.days_since_contact")

# Sentinel value when no events exist
NO_EVENTS_VALUE = Decimal(9999)


async def run_days_since_contact() -> None:
    """Compute days_since_last_contact for all active customers."""
    logger.info("Starting days-since-contact computation")
    start = time.monotonic()

    async for session in get_session():
        try:
            await _compute_all(session)
        except Exception as exc:
            logger.error("Days-since-contact computation failed", error=str(exc))
        break  # Exit the async generator to ensure session cleanup

    elapsed = time.monotonic() - start
    logger.info("Days-since-contact computation completed", duration_seconds=round(elapsed, 2))


async def _compute_all(session: AsyncSession) -> None:
    """Core logic: iterate customers and compute days since last contact."""
    # Load metric definition
    metric_def_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_def = await metric_def_repo.get_by_name("days_since_last_contact")
    if metric_def is None:
        logger.warning("Metric definition 'days_since_last_contact' not found")
        return

    # Load all active customers
    result = await session.execute(select(CustomerModel).where(CustomerModel.deleted_at.is_(None)))
    customers = result.scalars().all()

    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    now = datetime.now(UTC)

    processed = 0
    errors = 0

    for customer in customers:
        try:
            # Find the most recent event for this customer
            latest_result = await session.execute(
                select(func.max(EventModel.occurred_at)).where(
                    EventModel.customer_id == customer.id,
                    EventModel.deleted_at.is_(None),
                )
            )
            latest_event_at = latest_result.scalar()

            if latest_event_at is None:
                value = NO_EVENTS_VALUE
            else:
                # Ensure timezone-aware comparison
                if latest_event_at.tzinfo is None:
                    latest_event_at = latest_event_at.replace(tzinfo=UTC)
                delta = now - latest_event_at
                value = Decimal(delta.days)

            # Upsert customer_metrics
            await metric_repo.upsert(customer.id, metric_def.id, value)

            # Append to history
            await history_repo.append(customer.id, metric_def.id, value)

            processed += 1
        except Exception as exc:
            errors += 1
            logger.error(
                "Failed to compute days-since-contact for customer",
                customer_id=str(customer.id),
                error=str(exc),
            )

    logger.info(
        "Days-since-contact computation completed",
        processed=processed,
        errors=errors,
    )
