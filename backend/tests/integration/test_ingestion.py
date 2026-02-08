"""Integration tests for the ingestion webhook endpoint."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestIngestion:
    async def test_ingest_missing_token_header(self, client, seeded_roles):
        resp = await client.post(
            "/hooks/ingest",
            json={
                "event_type": "support_ticket",
                "customer_identifier": "Acme Corp",
                "title": "Test ticket",
                "occurred_at": "2024-06-15T00:00:00Z",
            },
        )
        assert resp.status_code == 401

    async def test_ingest_success(self, client, db, seeded_roles):
        """Test ingestion with a mocked broker (no real RabbitMQ)."""
        import hashlib
        from uuid import uuid4

        from app.infrastructure.models.source import SourceModel

        # Create a source with known token hash
        token = "test-source-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        source = SourceModel(
            id=uuid4(),
            name="test-source",
            api_token_hash=token_hash,
            is_active=True,
        )
        db.add(source)
        await db.flush()

        # Mock the broker and Redis to avoid needing RabbitMQ/Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with (
            patch("app.api.routes.ingestion.get_publisher") as mock_get_pub,
            patch("app.api.routes.ingestion.get_redis", return_value=mock_redis),
        ):
            mock_publisher = AsyncMock()
            mock_publisher.publish = AsyncMock()
            mock_get_pub.return_value = mock_publisher

            resp = await client.post(
                "/hooks/ingest",
                json={
                    "event_type": "support_ticket",
                    "customer_identifier": "Acme Corp",
                    "title": "Test ticket from ingestion",
                    "occurred_at": "2024-06-15T00:00:00Z",
                },
                headers={"X-Source-Token": token},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "accepted"
        assert "event_id" in data
