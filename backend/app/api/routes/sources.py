"""Source management routes for the source integration context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import require_permission
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.source import (
    SourceCreateRequest,
    SourceCreateResponse,
    SourceDetailSchema,
    SourceSummarySchema,
    SourceUpdateRequest,
)
from app.api.service_factories import get_source_service
from app.application.services.source import SourceService
from app.core.context import CallerContext
from app.core.types import Pagination

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SourceSummarySchema])
async def list_sources(
    ctx: CallerContext = Depends(require_permission("sources.read")),
    service: SourceService = Depends(get_source_service),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SourceSummarySchema]:
    """List all registered data sources."""
    result = await service.list_sources(
        pagination=Pagination(cursor=cursor, limit=limit),
        ctx=ctx,
    )
    return PaginatedResponse(
        data=[SourceSummarySchema.model_validate(dto, from_attributes=True) for dto in result.data],
        pagination={
            "total": result.total,
            "limit": limit,
            "has_next": result.has_next,
            "next_cursor": result.next_cursor,
        },
    )


@router.get("/{source_id}", response_model=SourceDetailSchema)
async def get_source(
    source_id: UUID,
    ctx: CallerContext = Depends(require_permission("sources.read")),
    service: SourceService = Depends(get_source_service),
) -> SourceDetailSchema:
    """Get a single source by ID."""
    result = await service.get_source(source_id, ctx=ctx)
    return SourceDetailSchema.model_validate(result, from_attributes=True)


@router.post("", response_model=SourceCreateResponse, status_code=201)
async def create_source(
    body: SourceCreateRequest,
    ctx: CallerContext = Depends(require_permission("sources.manage")),
    service: SourceService = Depends(get_source_service),
) -> SourceCreateResponse:
    """Register a new data source and generate an API token.

    The API token is returned only in this response and cannot be retrieved again.
    """
    result = await service.create_source(
        name=body.name,
        description=body.description,
        ctx=ctx,
    )
    return SourceCreateResponse.model_validate(result, from_attributes=True)


@router.patch("/{source_id}", response_model=SourceSummarySchema)
async def update_source(
    source_id: UUID,
    body: SourceUpdateRequest,
    ctx: CallerContext = Depends(require_permission("sources.manage")),
    service: SourceService = Depends(get_source_service),
) -> SourceSummarySchema:
    """Update source name, description, or active status."""
    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    result = await service.update_source(
        source_id=source_id,
        updates=updates,
        ctx=ctx,
    )
    return SourceSummarySchema.model_validate(result, from_attributes=True)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    ctx: CallerContext = Depends(require_permission("sources.manage")),
    service: SourceService = Depends(get_source_service),
) -> Response:
    """Soft-delete a data source."""
    await service.delete_source(
        source_id=source_id,
        ctx=ctx,
    )
    return Response(status_code=204)
