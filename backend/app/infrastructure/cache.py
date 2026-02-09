import json

import redis.asyncio as aioredis

from app.config import get_settings


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

    async def incr(self, key: str) -> int:
        """Atomically increment a key and return the new value."""
        return await self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> None:
        """Set a TTL on an existing key."""
        await self._client.expire(key, seconds)

    async def ping(self) -> bool:
        """Ping Redis to check connectivity."""
        return await self._client.ping()

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        await self._client.aclose()


class _RedisHolder:
    """Module-level state holder. Avoids ``global`` keyword."""

    client: AsyncRedisClient | None = None


_holder = _RedisHolder()


def get_redis() -> AsyncRedisClient:
    """Return a singleton AsyncRedisClient instance."""
    if _holder.client is None:
        settings = get_settings()
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
        )
        _holder.client = AsyncRedisClient(client)
    return _holder.client


async def close_redis() -> None:
    """Close the global Redis client. Called at shutdown."""
    if _holder.client is not None:
        await _holder.client.close()
        _holder.client = None
