"""Metrics worker: recalculates affected customer metrics on new events.

Consumes messages from ``q.metrics``.  After each event is ingested the
metrics worker recomputes ``support_tickets_last_30d`` and
``days_since_last_contact`` for the affected customer, upserting into
``customer_metrics`` and appending a snapshot to
``customer_metric_history``.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.logging import get_logger
from app.infrastructure.models.event import EventModel
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)
from workers._resolve import resolve_customer

logger = get_logger("worker.metrics")


async def process_message(message: dict, session: AsyncSession) -> None:
    """Recalculate affected metrics for the customer of a new event."""
    payload = message.get("payload", {})
    customer_identifier = payload.get("customer_identifier", "")

    # Resolve customer
    customer_id = await resolve_customer(session, customer_identifier)
    if customer_id is None:
        logger.warning(
            "Cannot recompute metrics: customer not found",
            identifier=customer_identifier,
        )
        return

    # Recompute support_tickets_last_30d
    await _recompute_support_tickets(session, customer_id)

    # Recompute days_since_last_contact
    await _recompute_days_since_contact(session, customer_id)

    logger.info("Metrics recomputed", customer_id=str(customer_id))


async def _recompute_support_tickets(session: AsyncSession, customer_id: UUID) -> None:
    """Count support tickets in the last 30 days and upsert the metric."""
    metric_def_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_def = await metric_def_repo.get_by_name("support_tickets_last_30d")
    if metric_def is None:
        logger.warning("Metric definition 'support_tickets_last_30d' not found")
        return

    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    count_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.event_type == "support_ticket",
            EventModel.occurred_at >= thirty_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    count = count_result.scalar() or 0
    value = Decimal(count)

    # Upsert current metric
    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    await metric_repo.upsert(customer_id, metric_def.id, value)

    # Append to history
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    await history_repo.append(customer_id, metric_def.id, value)


async def _recompute_days_since_contact(session: AsyncSession, customer_id: UUID) -> None:
    """Calculate days since last contact (now - max(occurred_at))."""
    metric_def_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_def = await metric_def_repo.get_by_name("days_since_last_contact")
    if metric_def is None:
        logger.warning("Metric definition 'days_since_last_contact' not found")
        return

    result = await session.execute(
        select(func.max(EventModel.occurred_at)).where(
            EventModel.customer_id == customer_id,
            EventModel.deleted_at.is_(None),
        )
    )
    latest_event_at = result.scalar()

    if latest_event_at is None:
        value = Decimal(9999)
    else:
        # Ensure timezone-aware comparison
        now = datetime.now(UTC)
        if latest_event_at.tzinfo is None:
            latest_event_at = latest_event_at.replace(tzinfo=UTC)
        delta = now - latest_event_at
        value = Decimal(delta.days)

    # Upsert current metric
    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    await metric_repo.upsert(customer_id, metric_def.id, value)

    # Append to history
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    await history_repo.append(customer_id, metric_def.id, value)
