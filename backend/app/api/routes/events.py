"""Event routes for activity tracking context."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.api.schemas.common import PaginatedResponse, PaginationMeta
from app.api.schemas.event import EventSummarySchema
from app.api.service_factories import get_event_service
from app.application.services.event import EventService
from app.core.context import CallerContext
from app.core.types import Pagination

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EventSummarySchema])
async def list_events(
    customer_id: UUID,
    event_type: str | None = Query(None, description="Filter by event type"),
    since: datetime | None = Query(None, description="Events after this time (ISO 8601)"),
    until: datetime | None = Query(None, description="Events before this time (ISO 8601)"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by occurred_at"),
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    ctx: CallerContext = Depends(require_permission("events.read")),
    service: EventService = Depends(get_event_service),
) -> PaginatedResponse[EventSummarySchema]:
    """List events for a customer with optional filters and cursor-based pagination."""
    result = await service.list_events(
        customer_id=customer_id,
        event_type=event_type,
        since=since,
        until=until,
        order=order,
        pagination=Pagination(cursor=cursor, limit=limit),
        ctx=ctx,
    )
    return PaginatedResponse(
        data=[EventSummarySchema(**dto.__dict__) for dto in result.data],
        pagination=PaginationMeta(
            total=result.total,
            limit=limit,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        ),
    )
