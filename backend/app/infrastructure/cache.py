import json

import redis.asyncio as aioredis

from app.config import get_settings

_redis_client: "AsyncRedisClient | None" = None


class AsyncRedisClient:
    """Thin async wrapper around redis.asyncio for cache operations."""

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        """Get a value by key. Returns None if key does not exist."""
        value = await self._client.get(key)
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else value

    async def set(
        self,
        key: str,
        value: str | dict | list,
        ttl: int | None = None,
    ) -> None:
        """Set a key-value pair with an optional TTL in seconds.

        If value is a dict or list it will be JSON-serialised before storing.
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if ttl is not None:
            await self._client.set(key, value, ex=ttl)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check whether a key exists."""
        return bool(await self._client.exists(key))

    async def ping(self) -> bool:
        """Ping Redis to check connectivity."""
        return await self._client.ping()

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        await self._client.aclose()


def get_redis() -> AsyncRedisClient:
    """Return a singleton AsyncRedisClient instance."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
        )
        _redis_client = AsyncRedisClient(client)
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis client. Called at shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
