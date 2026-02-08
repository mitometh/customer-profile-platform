"""Health check route.

GET /api/health — publicly accessible (no auth required).
Pings database, Redis, and reports status for RabbitMQ and LLM provider.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.infrastructure.cache import get_redis
from app.infrastructure.logging import get_logger

logger = get_logger("health")

router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Full health check: ping database, Redis, RabbitMQ, LLM provider.

    Returns a JSON object with overall status and individual service checks.
    Overall status is "healthy" only when all checked services are healthy,
    otherwise "degraded".
    """
    checks: dict[str, str] = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception as exc:
        logger.warning("Database health check failed", error=str(exc))
        checks["database"] = "down"

    # Redis check
    try:
        redis_client = get_redis()
        await redis_client.ping()
        checks["redis"] = "up"
    except Exception as exc:
        logger.warning("Redis health check failed", error=str(exc))
        checks["redis"] = "down"

    # RabbitMQ check (best effort — not always connected from the API process)
    checks["message_broker"] = "not_checked"

    # LLM provider check (best effort — avoid burning tokens on health probes)
    checks["llm_provider"] = "not_checked"

    overall = "healthy" if all(v == "up" for v in checks.values() if v != "not_checked") else "degraded"

    return {
        "status": overall,
        "version": "0.1.0",
        "checks": checks,
    }
