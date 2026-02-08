"""Source management routes for the source integration context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDTO, get_db, require_permission
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.source import (
    SourceCreateRequest,
    SourceCreateResponse,
    SourceDetailSchema,
    SourceSummarySchema,
    SourceUpdateRequest,
)
from app.application.services.source import SourceService
from app.core.types import Pagination
from app.infrastructure.cache import get_redis
from app.infrastructure.repositories.source import (
    RedisTokenCache,
    SqlAlchemySourceRepository,
)

router = APIRouter()


def _build_service(db: AsyncSession) -> SourceService:
    """Construct a SourceService with its dependencies."""
    source_repo = SqlAlchemySourceRepository(db)
    token_cache = RedisTokenCache(get_redis())
    return SourceService(source_repo=source_repo, token_cache=token_cache)


@router.get("", response_model=PaginatedResponse[SourceSummarySchema])
async def list_sources(
    user: CurrentUserDTO = Depends(require_permission("sources.read")),
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SourceSummarySchema]:
    """List all registered data sources."""
    service = _build_service(db)
    result = await service.list_sources(
        pagination=Pagination(cursor=cursor, limit=limit),
        permissions=user.permissions,
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
    user: CurrentUserDTO = Depends(require_permission("sources.read")),
    db: AsyncSession = Depends(get_db),
) -> SourceDetailSchema:
    """Get a single source by ID."""
    service = _build_service(db)
    result = await service.get_source(source_id, user.permissions)
    return SourceDetailSchema.model_validate(result, from_attributes=True)


@router.post("", response_model=SourceCreateResponse, status_code=201)
async def create_source(
    body: SourceCreateRequest,
    user: CurrentUserDTO = Depends(require_permission("sources.manage")),
    db: AsyncSession = Depends(get_db),
) -> SourceCreateResponse:
    """Register a new data source and generate an API token.

    The API token is returned only in this response and cannot be retrieved again.
    """
    service = _build_service(db)
    result = await service.create_source(
        name=body.name,
        description=body.description,
        permissions=user.permissions,
        created_by=user.id,
    )
    return SourceCreateResponse.model_validate(result, from_attributes=True)


@router.patch("/{source_id}", response_model=SourceSummarySchema)
async def update_source(
    source_id: UUID,
    body: SourceUpdateRequest,
    user: CurrentUserDTO = Depends(require_permission("sources.manage")),
    db: AsyncSession = Depends(get_db),
) -> SourceSummarySchema:
    """Update source name, description, or active status."""
    service = _build_service(db)
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
        permissions=user.permissions,
        updated_by=user.id,
    )
    return SourceSummarySchema.model_validate(result, from_attributes=True)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    user: CurrentUserDTO = Depends(require_permission("sources.manage")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete a data source."""
    service = _build_service(db)
    await service.delete_source(
        source_id=source_id,
        permissions=user.permissions,
        deleted_by=user.id,
    )
    return Response(status_code=204)
