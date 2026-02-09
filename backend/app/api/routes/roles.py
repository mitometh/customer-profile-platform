"""Role & permission management routes for the identity-access context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import require_permission
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.role import (
    PermissionSchema,
    RoleCreateRequest,
    RoleDetailSchema,
    RoleSummarySchema,
    RoleUpdateRequest,
)
from app.api.service_factories import get_role_service
from app.application.services.role import RoleService
from app.core.context import CallerContext
from app.core.types import Pagination

roles_router = APIRouter()
permissions_router = APIRouter()


# ============================================================
# PERMISSIONS
# ============================================================


@permissions_router.get("", response_model=list[PermissionSchema])
async def list_permissions(
    ctx: CallerContext = Depends(require_permission("roles.read")),
    service: RoleService = Depends(get_role_service),
) -> list[PermissionSchema]:
    """List all available permissions."""
    result = await service.list_permissions(ctx=ctx)
    return [PermissionSchema.model_validate(dto, from_attributes=True) for dto in result]


# ============================================================
# ROLES
# ============================================================


@roles_router.get("", response_model=PaginatedResponse[RoleSummarySchema])
async def list_roles(
    ctx: CallerContext = Depends(require_permission("roles.read")),
    service: RoleService = Depends(get_role_service),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[RoleSummarySchema]:
    """List all roles with permission counts."""
    result = await service.list_roles(
        pagination=Pagination(cursor=cursor, limit=limit),
        ctx=ctx,
    )
    return PaginatedResponse(
        data=[RoleSummarySchema.model_validate(dto, from_attributes=True) for dto in result.data],
        pagination={
            "total": result.total,
            "limit": limit,
            "has_next": result.has_next,
            "next_cursor": result.next_cursor,
        },
    )


@roles_router.get("/{role_id}", response_model=RoleDetailSchema)
async def get_role(
    role_id: UUID,
    ctx: CallerContext = Depends(require_permission("roles.read")),
    service: RoleService = Depends(get_role_service),
) -> RoleDetailSchema:
    """Get role detail with full permission list."""
    result = await service.get_role(role_id, ctx=ctx)
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.post("", response_model=RoleDetailSchema, status_code=201)
async def create_role(
    body: RoleCreateRequest,
    ctx: CallerContext = Depends(require_permission("roles.manage")),
    service: RoleService = Depends(get_role_service),
) -> RoleDetailSchema:
    """Create a new custom role."""
    result = await service.create_role(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        permission_ids=body.permissions,
        ctx=ctx,
    )
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.patch("/{role_id}", response_model=RoleDetailSchema)
async def update_role(
    role_id: UUID,
    body: RoleUpdateRequest,
    ctx: CallerContext = Depends(require_permission("roles.manage")),
    service: RoleService = Depends(get_role_service),
) -> RoleDetailSchema:
    """Update role details and/or permission assignments."""
    updates: dict = {}
    if body.display_name is not None:
        updates["display_name"] = body.display_name
    if body.description is not None:
        updates["description"] = body.description
    if body.permissions is not None:
        updates["permissions"] = body.permissions
    result = await service.update_role(
        role_id=role_id,
        updates=updates,
        ctx=ctx,
    )
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: UUID,
    ctx: CallerContext = Depends(require_permission("roles.manage")),
    service: RoleService = Depends(get_role_service),
) -> Response:
    """Soft-delete a custom role."""
    await service.delete_role(
        role_id=role_id,
        ctx=ctx,
    )
    return Response(status_code=204)
