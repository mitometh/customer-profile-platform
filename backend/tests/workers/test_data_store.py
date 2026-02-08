"""Integration tests for the data_store worker message processing."""

from datetime import UTC, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.infrastructure.models.event import EventModel
from workers.data_store import process_message

pytestmark = pytest.mark.asyncio


class TestDataStoreWorker:
    async def test_process_message_creates_event(self, db, sample_customer):
        event_id = str(uuid4())
        message = {
            "event_id": event_id,
            "source_id": None,
            "source_name": "test",
            "payload": {
                "event_type": "support_ticket",
                "customer_identifier": "Acme Corp",
                "title": "Worker test ticket",
                "description": "Created by test",
                "occurred_at": "2024-06-20T10:00:00Z",
                "data": {"priority": "high"},
            },
            "received_at": datetime.now(UTC).isoformat(),
        }

        await process_message(message, db)

        # Verify event was persisted
        result = await db.execute(select(EventModel).where(EventModel.title == "Worker test ticket"))
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.event_type == "support_ticket"
        assert event.customer_id == sample_customer.id

    async def test_process_message_unknown_customer(self, db, sample_customer):
        """Events with unresolvable customer should still be persisted (customer_id=NULL)."""
        message = {
            "event_id": str(uuid4()),
            "payload": {
                "event_type": "meeting",
                "customer_identifier": "Unknown Company",
                "title": "Orphan event",
            },
            "received_at": datetime.now(UTC).isoformat(),
        }

        await process_message(message, db)

        result = await db.execute(select(EventModel).where(EventModel.title == "Orphan event"))
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.customer_id is None
