"""Alerts worker: checks metric thresholds and logs warnings.

Consumes messages from ``q.alerts``.  For the assignment scope this
worker only performs logging-based alerting (no external notifications).

Thresholds checked:
- health_score < 40 -> "At-risk customer detected"
- support_tickets_last_30d > 5 -> "High ticket volume"
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.logging import get_logger
from app.infrastructure.models.metric import (
    CustomerMetricModel,
    MetricDefinitionModel,
)
from workers._resolve import resolve_customer

logger = get_logger("worker.alerts")

# Alert thresholds
HEALTH_SCORE_AT_RISK = Decimal("40")
HIGH_TICKET_VOLUME = Decimal("5")


async def process_message(message: dict, session: AsyncSession) -> None:
    """Check alert thresholds for the customer's metrics."""
    payload = message.get("payload", {})
    customer_identifier = payload.get("customer_identifier", "")

    # Resolve customer
    customer_id = await resolve_customer(session, customer_identifier)
    if customer_id is None:
        return

    # Fetch current metrics for the customer
    result = await session.execute(
        select(CustomerMetricModel, MetricDefinitionModel.name)
        .join(
            MetricDefinitionModel,
            CustomerMetricModel.metric_definition_id == MetricDefinitionModel.id,
        )
        .where(
            CustomerMetricModel.customer_id == customer_id,
            CustomerMetricModel.deleted_at.is_(None),
        )
    )
    rows = result.all()

    for metric_row, metric_name in rows:
        value = metric_row.metric_value

        if metric_name == "health_score" and value < HEALTH_SCORE_AT_RISK:
            logger.warning(
                "At-risk customer detected",
                customer_id=str(customer_id),
                health_score=str(value),
                threshold=str(HEALTH_SCORE_AT_RISK),
            )

        if metric_name == "support_tickets_last_30d" and value > HIGH_TICKET_VOLUME:
            logger.warning(
                "High ticket volume",
                customer_id=str(customer_id),
                ticket_count=str(value),
                threshold=str(HIGH_TICKET_VOLUME),
            )

    logger.info("Alert check completed", customer_id=str(customer_id))
