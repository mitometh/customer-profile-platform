"""Scheduled job: compute composite health score (0-100) for all active customers.

Runs daily at 02:15 UTC via the scheduler.

Formula:
    Base score: 70
    + Recent activity bonus:
        +15 if any event in last 7 days
        +5  if any event in last 30 days (but not in last 7)
    - Support ticket penalty:
        -5 per support ticket in last 30 days (capped at -25)
    Clamped to [0, 100].

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

logger = get_logger("job.health_score")

# Formula constants
BASE_SCORE = 70
RECENT_7D_BONUS = 15
RECENT_30D_BONUS = 5
TICKET_PENALTY_PER = 5
TICKET_PENALTY_CAP = 25
SCORE_MIN = 0
SCORE_MAX = 100


async def run_health_score() -> None:
    """Compute composite health score for all active customers."""
    logger.info("Starting health score computation")
    start = time.monotonic()

    async for session in get_session():
        try:
            await _compute_all(session)
        except Exception as exc:
            logger.error("Health score computation failed", error=str(exc))
        break  # Exit the async generator to ensure session cleanup

    elapsed = time.monotonic() - start
    logger.info("Health score computation completed", duration_seconds=round(elapsed, 2))


async def _compute_all(session: AsyncSession) -> None:
    """Core logic: iterate customers and compute health scores."""
    # Load metric definition
    metric_def_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_def = await metric_def_repo.get_by_name("health_score")
    if metric_def is None:
        logger.warning("Metric definition 'health_score' not found")
        return

    # Load all active customers
    result = await session.execute(select(CustomerModel).where(CustomerModel.deleted_at.is_(None)))
    customers = result.scalars().all()

    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)

    now = datetime.now(UTC)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    processed = 0
    errors = 0

    for customer in customers:
        try:
            score = await _compute_score(session, customer.id, seven_days_ago, thirty_days_ago)

            # Upsert customer_metrics
            await metric_repo.upsert(customer.id, metric_def.id, score)

            # Append to history
            await history_repo.append(customer.id, metric_def.id, score)

            processed += 1
        except Exception as exc:
            errors += 1
            logger.error(
                "Failed to compute health score for customer",
                customer_id=str(customer.id),
                error=str(exc),
            )

    logger.info(
        "Health score computation completed",
        processed=processed,
        errors=errors,
    )


async def _compute_score(
    session: AsyncSession,
    customer_id: object,
    seven_days_ago: datetime,
    thirty_days_ago: datetime,
) -> Decimal:
    """Compute the composite health score for a single customer.

    Returns:
        Decimal value clamped to [0, 100].
    """
    score = BASE_SCORE

    # --- Recent activity bonus ---
    events_7d_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.occurred_at >= seven_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    events_7d = events_7d_result.scalar() or 0

    if events_7d > 0:
        score += RECENT_7D_BONUS
    else:
        # Check 30-day window only if no 7-day activity
        events_30d_result = await session.execute(
            select(func.count(EventModel.id)).where(
                EventModel.customer_id == customer_id,
                EventModel.occurred_at >= thirty_days_ago,
                EventModel.deleted_at.is_(None),
            )
        )
        events_30d = events_30d_result.scalar() or 0
        if events_30d > 0:
            score += RECENT_30D_BONUS

    # --- Support ticket penalty ---
    tickets_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.event_type == "support_ticket",
            EventModel.occurred_at >= thirty_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    ticket_count = tickets_result.scalar() or 0
    ticket_penalty = min(ticket_count * TICKET_PENALTY_PER, TICKET_PENALTY_CAP)
    score -= ticket_penalty

    # Clamp to [0, 100]
    score = max(SCORE_MIN, min(SCORE_MAX, score))

    return Decimal(score)
