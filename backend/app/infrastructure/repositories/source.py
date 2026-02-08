"""Source repository and Redis token cache for source integration context."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache import AsyncRedisClient
from app.infrastructure.models.source import SourceModel
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemySourceRepository(BaseRepository[SourceModel]):
    """Data-access layer for data sources."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SourceModel)

    async def get_by_name(self, name: str) -> SourceModel | None:
        """Fetch a source by its unique name, excluding soft-deleted rows."""
        stmt = select(SourceModel).where(SourceModel.name == name)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> SourceModel | None:
        """Fetch a source by its API token hash, excluding soft-deleted rows."""
        stmt = select(SourceModel).where(
            SourceModel.api_token_hash == token_hash,
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class RedisTokenCache:
    """Redis-based cache for source token validation.

    Caches the mapping from a SHA256 token hash to source info
    (id, name, is_active) with a configurable TTL (default 5 minutes).
    """

    _KEY_PREFIX = "source_token:"

    def __init__(self, redis_client: AsyncRedisClient) -> None:
        self._redis = redis_client

    async def validate_token(self, token_hash: str) -> dict | None:
        """Check Redis cache for a previously validated token.

        Returns:
            A dict with source info (id, name, is_active) if cached, else None.
        """
        key = f"{self._KEY_PREFIX}{token_hash}"
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def cache_token(
        self,
        token_hash: str,
        source_info: dict,
        ttl: int = 300,
    ) -> None:
        """Store source info in Redis with a TTL.

        Args:
            token_hash: The SHA256 hash of the API token.
            source_info: Dict containing id, name, is_active.
            ttl: Time-to-live in seconds (default 300 = 5 minutes).
        """
        key = f"{self._KEY_PREFIX}{token_hash}"
        await self._redis.set(key, source_info, ttl=ttl)

    async def invalidate_token(self, token_hash: str) -> None:
        """Remove a cached token entry from Redis."""
        key = f"{self._KEY_PREFIX}{token_hash}"
        await self._redis.delete(key)
