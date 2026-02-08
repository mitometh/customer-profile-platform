"""Role & permission management routes for the identity-access context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDTO, get_db, require_permission
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.role import (
    PermissionSchema,
    RoleCreateRequest,
    RoleDetailSchema,
    RoleSummarySchema,
    RoleUpdateRequest,
)
from app.application.services.role import RoleService
from app.core.types import Pagination
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository

roles_router = APIRouter()
permissions_router = APIRouter()


def _build_service(db: AsyncSession) -> RoleService:
    """Construct a RoleService with its dependencies."""
    role_repo = SqlAlchemyRoleRepository(db)
    return RoleService(role_repo=role_repo)


# ============================================================
# PERMISSIONS
# ============================================================


@permissions_router.get("", response_model=list[PermissionSchema])
async def list_permissions(
    user: CurrentUserDTO = Depends(require_permission("roles.read")),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionSchema]:
    """List all available permissions."""
    service = _build_service(db)
    result = await service.list_permissions(permissions=user.permissions)
    return [PermissionSchema.model_validate(dto, from_attributes=True) for dto in result]


# ============================================================
# ROLES
# ============================================================


@roles_router.get("", response_model=PaginatedResponse[RoleSummarySchema])
async def list_roles(
    user: CurrentUserDTO = Depends(require_permission("roles.read")),
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[RoleSummarySchema]:
    """List all roles with permission counts."""
    service = _build_service(db)
    result = await service.list_roles(
        pagination=Pagination(cursor=cursor, limit=limit),
        permissions=user.permissions,
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
    user: CurrentUserDTO = Depends(require_permission("roles.read")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailSchema:
    """Get role detail with full permission list."""
    service = _build_service(db)
    result = await service.get_role(role_id, user.permissions)
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.post("", response_model=RoleDetailSchema, status_code=201)
async def create_role(
    body: RoleCreateRequest,
    user: CurrentUserDTO = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailSchema:
    """Create a new custom role."""
    service = _build_service(db)
    result = await service.create_role(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        permission_ids=body.permissions,
        permissions=user.permissions,
    )
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.patch("/{role_id}", response_model=RoleDetailSchema)
async def update_role(
    role_id: UUID,
    body: RoleUpdateRequest,
    user: CurrentUserDTO = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailSchema:
    """Update role details and/or permission assignments."""
    service = _build_service(db)
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
        permissions=user.permissions,
    )
    return RoleDetailSchema.model_validate(result, from_attributes=True)


@roles_router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: UUID,
    user: CurrentUserDTO = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete a custom role."""
    service = _build_service(db)
    await service.delete_role(
        role_id=role_id,
        permissions=user.permissions,
        deleted_by=user.id,
    )
    return Response(status_code=204)
