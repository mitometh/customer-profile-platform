"""Data-store worker: persists ingested events to the database.

Consumes messages from ``q.data-store``, resolves the customer identifier
to a UUID, and inserts an EventModel row.  If the customer cannot be
resolved the event is still persisted with ``customer_id=NULL`` and a
warning is logged.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.logging import get_logger
from app.infrastructure.models.event import EventModel
from workers._resolve import resolve_customer

logger = get_logger("worker.data_store")


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


async def process_message(message: dict, session: AsyncSession) -> None:
    """Process an ingested event: resolve customer, persist event to DB.

    Message format (EventEnvelope)::

        {
            "event_id": "uuid",
            "source_id": "uuid",
            "source_name": "salesforce",
            "payload": {
                "event_type": "support_ticket",
                "customer_identifier": "Acme Corp",
                "title": "API issue",
                "description": "...",
                "occurred_at": "2025-01-15T10:30:00Z",
                "data": {},
            },
            "received_at": "2025-01-15T10:30:05Z",
        }
    """
    payload = message.get("payload", {})
    source_id_raw = message.get("source_id")

    # Resolve customer by identifier
    customer_identifier = payload.get("customer_identifier", "")
    customer_id = await resolve_customer(session, customer_identifier)

    if customer_id is None:
        logger.warning(
            "Could not resolve customer",
            identifier=customer_identifier,
        )

    # Determine event ID
    event_id: UUID
    if "event_id" in message:
        try:
            event_id = UUID(message["event_id"])
        except (ValueError, TypeError):
            event_id = uuid4()
    else:
        event_id = uuid4()

    # Determine source_id
    source_id: UUID | None = None
    if source_id_raw:
        try:
            source_id = UUID(source_id_raw)
        except (ValueError, TypeError):
            source_id = None

    # Build and persist the event
    event = EventModel(
        id=event_id,
        customer_id=customer_id,
        source_id=source_id,
        event_type=payload.get("event_type", "unknown"),
        title=payload.get("title", "Untitled"),
        description=payload.get("description"),
        occurred_at=_parse_datetime(payload.get("occurred_at")) or datetime.now(UTC),
        data=payload.get("data"),
    )

    session.add(event)
    await session.flush()

    logger.info(
        "Event persisted",
        event_id=str(event.id),
        customer_id=str(customer_id),
    )
