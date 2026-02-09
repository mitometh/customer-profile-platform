"""Ingestion webhook route for external data sources."""

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.api.schemas.ingestion import IngestRequest, IngestResponse
from app.api.service_factories import get_ingestion_service
from app.application.services.ingestion import IngestionService
from app.core.exceptions import UnauthorizedError

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_event(
    body: IngestRequest,
    x_source_token: str | None = Header(default=None),
    service: IngestionService = Depends(get_ingestion_service),
) -> JSONResponse:
    """Receive data from an external source via webhook.

    Authentication is via the X-Source-Token header (not JWT).
    Validates the token, publishes the event to RabbitMQ, and returns 202 Accepted.
    """
    if x_source_token is None:
        raise UnauthorizedError("Missing X-Source-Token header")

    payload = body.model_dump(mode="json")
    event_id = await service.validate_and_publish(
        token=x_source_token,
        payload=payload,
    )

    return JSONResponse(
        status_code=202,
        content=IngestResponse(event_id=event_id).model_dump(),
    )
