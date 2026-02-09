"""Scheduled job: compute composite health score (0-100) for all active customers.

Runs daily at 02:15 UTC via the scheduler.

Formula:
    Base score: 70
    +10 if any meeting event in the last 30 days
    +10 if any usage_event in the last 30 days
    -5 per support ticket in the last 30 days (uncapped)
    -10 if no events at all in the last 14 days
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

# Formula constants — aligned with seeds/seed.py
BASE_SCORE = 70
MEETING_BONUS = 10
USAGE_BONUS = 10
TICKET_PENALTY_PER = 5
NO_RECENT_PENALTY = 10
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
    fourteen_days_ago = now - timedelta(days=14)
    thirty_days_ago = now - timedelta(days=30)

    processed = 0
    errors = 0

    for customer in customers:
        try:
            score = await _compute_score(session, customer.id, fourteen_days_ago, thirty_days_ago)

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
    fourteen_days_ago: datetime,
    thirty_days_ago: datetime,
) -> Decimal:
    """Compute the composite health score for a single customer.

    Formula (aligned with seed script):
        Base 70
        +10 if meetings in last 30d
        +10 if usage_events in last 30d
        -5 per support ticket in last 30d
        -10 if no events in last 14d
        Clamped [0, 100]

    Returns:
        Decimal value clamped to [0, 100].
    """
    score = BASE_SCORE

    # --- Meeting bonus: +10 if any meeting in last 30d ---
    meetings_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.event_type == "meeting",
            EventModel.occurred_at >= thirty_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    has_meetings = (meetings_result.scalar() or 0) > 0
    if has_meetings:
        score += MEETING_BONUS

    # --- Usage event bonus: +10 if any usage_event in last 30d ---
    usage_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.event_type == "usage_event",
            EventModel.occurred_at >= thirty_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    has_usage = (usage_result.scalar() or 0) > 0
    if has_usage:
        score += USAGE_BONUS

    # --- Support ticket penalty: -5 per ticket in last 30d (uncapped) ---
    tickets_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.event_type == "support_ticket",
            EventModel.occurred_at >= thirty_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    ticket_count = tickets_result.scalar() or 0
    score -= ticket_count * TICKET_PENALTY_PER

    # --- No recent activity penalty: -10 if no events in last 14d ---
    recent_result = await session.execute(
        select(func.count(EventModel.id)).where(
            EventModel.customer_id == customer_id,
            EventModel.occurred_at >= fourteen_days_ago,
            EventModel.deleted_at.is_(None),
        )
    )
    has_recent = (recent_result.scalar() or 0) > 0
    if not has_recent:
        score -= NO_RECENT_PENALTY

    # Clamp to [0, 100]
    score = max(SCORE_MIN, min(SCORE_MAX, score))

    return Decimal(score)
