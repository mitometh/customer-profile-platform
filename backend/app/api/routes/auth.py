"""Auth and user management routes for identity & access context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUserDTO, get_current_user, require_permission
from app.api.schemas.auth import (
    CurrentUserSchema,
    LoginRequest,
    LoginResponse,
    UserCreateRequest,
    UserSummarySchema,
    UserUpdateRequest,
)
from app.api.schemas.common import PaginatedResponse
from app.api.service_factories import get_auth_service, get_user_service
from app.application.services.auth import AuthService
from app.application.services.user import UserService
from app.core.context import CallerContext
from app.core.types import Pagination

# Auth routes: mounted at /api/auth
router = APIRouter()

# User CRUD routes: mounted at /api/users
users_router = APIRouter()


# ------------------------------------------------------------------
# Auth endpoints (mounted under /api/auth)
# ------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate user and return JWT."""
    result = await service.login(body.email, body.password)
    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        user=CurrentUserSchema(
            id=result.user.id,
            email=result.user.email,
            full_name=result.user.full_name,
            role=result.user.role,
            permissions=result.user.permissions,
        ),
    )


@router.get("/me", response_model=CurrentUserSchema)
async def get_me(
    user: CurrentUserDTO = Depends(get_current_user),
) -> CurrentUserSchema:
    """Return the current authenticated user profile and permissions."""
    return CurrentUserSchema(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=user.permissions,
    )


# ------------------------------------------------------------------
# User management endpoints (mounted under /api/users)
# ------------------------------------------------------------------


@users_router.post("", response_model=UserSummarySchema, status_code=201)
async def create_user(
    body: UserCreateRequest,
    ctx: CallerContext = Depends(require_permission("users.manage")),
    service: UserService = Depends(get_user_service),
) -> UserSummarySchema:
    """Create a new user (admin only)."""
    result = await service.create_user(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        password=body.password,
        ctx=ctx,
    )
    return UserSummarySchema.model_validate(result, from_attributes=True)


@users_router.patch("/{user_id}", response_model=UserSummarySchema)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    ctx: CallerContext = Depends(require_permission("users.manage")),
    service: UserService = Depends(get_user_service),
) -> UserSummarySchema:
    """Update user role, active status, or name (admin only)."""
    updates: dict = {}
    if body.full_name is not None:
        updates["full_name"] = body.full_name
    if body.role_id is not None:
        updates["role_id"] = body.role_id
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    result = await service.update_user(
        user_id=user_id,
        updates=updates,
        ctx=ctx,
    )
    return UserSummarySchema.model_validate(result, from_attributes=True)


@users_router.get("", response_model=PaginatedResponse[UserSummarySchema])
async def list_users(
    ctx: CallerContext = Depends(require_permission("users.read")),
    service: UserService = Depends(get_user_service),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[UserSummarySchema]:
    """List all users with role assignments (admin only)."""
    result = await service.list_users(
        pagination=Pagination(cursor=cursor, limit=limit),
        ctx=ctx,
    )
    return PaginatedResponse(
        data=[UserSummarySchema.model_validate(dto, from_attributes=True) for dto in result.data],
        pagination={
            "total": result.total,
            "limit": limit,
            "has_next": result.has_next,
            "next_cursor": result.next_cursor,
        },
    )
