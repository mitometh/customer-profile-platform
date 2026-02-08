"""Auth and user management routes for identity & access context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDTO, get_current_user, get_db, require_permission
from app.api.schemas.auth import (
    CurrentUserSchema,
    LoginRequest,
    LoginResponse,
    UserCreateRequest,
    UserSummarySchema,
    UserUpdateRequest,
)
from app.api.schemas.common import PaginatedResponse
from app.application.services.auth import AuthService
from app.application.services.user import UserService
from app.core.types import Pagination
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository
from app.infrastructure.repositories.user import SqlAlchemyUserRepository

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
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return JWT."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    service = AuthService(user_repo=user_repo, role_repo=role_repo)
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
    user: CurrentUserDTO = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
) -> UserSummarySchema:
    """Create a new user (admin only)."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    service = UserService(user_repo=user_repo, role_repo=role_repo)
    result = await service.create_user(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        password=body.password,
        permissions=user.permissions,
    )
    return UserSummarySchema.model_validate(result, from_attributes=True)


@users_router.patch("/{user_id}", response_model=UserSummarySchema)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    user: CurrentUserDTO = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
) -> UserSummarySchema:
    """Update user role, active status, or name (admin only)."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    service = UserService(user_repo=user_repo, role_repo=role_repo)
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
        permissions=user.permissions,
        current_user_id=user.id,
    )
    return UserSummarySchema.model_validate(result, from_attributes=True)


@users_router.get("", response_model=PaginatedResponse[UserSummarySchema])
async def list_users(
    user: CurrentUserDTO = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[UserSummarySchema]:
    """List all users with role assignments (admin only)."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    service = UserService(user_repo=user_repo, role_repo=role_repo)
    result = await service.list_users(
        pagination=Pagination(cursor=cursor, limit=limit),
        permissions=user.permissions,
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
