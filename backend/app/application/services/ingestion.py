"""Ingestion service for the source integration context."""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.exceptions import UnauthorizedError
from app.infrastructure.broker import EXCHANGE_NAME, RabbitMQPublisher

logger = logging.getLogger(__name__)
from app.infrastructure.repositories.source import (
    RedisTokenCache,
    SqlAlchemySourceRepository,
)


class IngestionService:
    """Validates source tokens and publishes ingested events to the message broker."""

    def __init__(
        self,
        source_repo: SqlAlchemySourceRepository,
        token_cache: RedisTokenCache,
        broker: RabbitMQPublisher,
    ) -> None:
        self._source_repo = source_repo
        self._token_cache = token_cache
        self._broker = broker

    async def validate_and_publish(self, token: str, payload: dict[str, Any]) -> str:
        """Validate the source token and publish the event to RabbitMQ.

        Flow:
        1. Hash the raw token with SHA256.
        2. Check Redis cache for the token hash.
        3. On cache miss, query DB for a source with matching api_token_hash.
        4. Reject if not found or inactive.
        5. Cache the validated source info (TTL 5 min).
        6. Build an EventEnvelope and publish to the fanout exchange.

        Args:
            token: The raw API token from the X-Source-Token header.
            payload: The request body payload.

        Returns:
            The generated event_id (UUID string).

        Raises:
            UnauthorizedError: If the token is invalid or the source is inactive.
        """
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Check Redis cache first
        cached = await self._token_cache.validate_token(token_hash)

        if cached is not None:
            source_id = cached["id"]
            source_name = cached["name"]
            is_active = cached["is_active"]
        else:
            # Cache miss — query DB
            source = await self._source_repo.get_by_token_hash(token_hash)
            if source is None:
                raise UnauthorizedError("Invalid source token")

            source_id = str(source.id)
            source_name = source.name
            is_active = source.is_active

            # Cache the result
            await self._token_cache.cache_token(
                token_hash=token_hash,
                source_info={
                    "id": source_id,
                    "name": source_name,
                    "is_active": is_active,
                },
                ttl=300,
            )

        if not is_active:
            raise UnauthorizedError("Source is deactivated")

        # Build and publish EventEnvelope
        event_id = str(uuid4())
        envelope = {
            "event_id": event_id,
            "source_id": source_id,
            "source_name": source_name,
            "payload": payload,
            "received_at": datetime.now(UTC).isoformat(),
        }

        try:
            await self._broker.publish(exchange=EXCHANGE_NAME, message=envelope)
        except RuntimeError:
            logger.error("RabbitMQ publisher not connected — event %s was not published", event_id)
            raise

        return event_id
