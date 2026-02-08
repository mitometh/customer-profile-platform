"""Ingestion webhook route for external data sources."""

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.schemas.ingestion import IngestRequest, IngestResponse
from app.application.services.ingestion import IngestionService
from app.core.exceptions import UnauthorizedError
from app.infrastructure.broker import get_publisher
from app.infrastructure.cache import get_redis
from app.infrastructure.repositories.source import RedisTokenCache, SqlAlchemySourceRepository

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_event(
    body: IngestRequest,
    x_source_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Receive data from an external source via webhook.

    Authentication is via the X-Source-Token header (not JWT).
    Validates the token, publishes the event to RabbitMQ, and returns 202 Accepted.
    """
    if x_source_token is None:
        raise UnauthorizedError("Missing X-Source-Token header")

    # Wire up dependencies
    source_repo = SqlAlchemySourceRepository(db)
    token_cache = RedisTokenCache(get_redis())

    service = IngestionService(
        source_repo=source_repo,
        token_cache=token_cache,
        broker=get_publisher(),
    )

    payload = body.model_dump(mode="json")
    event_id = await service.validate_and_publish(
        token=x_source_token,
        payload=payload,
    )

    return JSONResponse(
        status_code=202,
        content=IngestResponse(event_id=event_id).model_dump(),
    )
