from collections.abc import AsyncGenerator, Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth import CurrentUserDTO
from app.core.context import CallerContext
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.infrastructure.database import get_read_session, get_session
from app.infrastructure.models.role import PermissionModel, RoleModel, RolePermissionModel
from app.infrastructure.models.user import UserModel
from app.infrastructure.security import decode_access_token

_bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (FastAPI dependency)."""
    async for session in get_session():
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-only async database session (FastAPI dependency)."""
    async for session in get_read_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUserDTO:
    """Extract and validate the JWT from the Authorization header.

    Loads the user from the database, verifies the account is active, resolves
    role-based permissions via the role_permissions join table, and returns a
    CurrentUserDTO.

    Raises:
        UnauthorizedError: missing/invalid token, inactive account, or user not found.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError(message="Token missing subject claim")

    try:
        user_id = UUID(user_id_str)
    except ValueError as exc:
        raise UnauthorizedError(message="Invalid user id in token") from exc

    # Load user
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None),
        ),
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(message="User not found")
    if not user.is_active:
        raise UnauthorizedError(message="User account is deactivated")

    # Load role name
    role_result = await db.execute(
        select(RoleModel.name).where(RoleModel.id == user.role_id),
    )
    role_name = role_result.scalar_one_or_none() or "unknown"

    # Load permissions via role_permissions join
    perm_result = await db.execute(
        select(PermissionModel.code)
        .join(
            RolePermissionModel,
            PermissionModel.id == RolePermissionModel.permission_id,
        )
        .where(RolePermissionModel.role_id == user.role_id),
    )
    permissions = list(perm_result.scalars().all())

    return CurrentUserDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role_name,
        permissions=permissions,
    )


def require_permission(permission: str) -> Callable:
    """Return a FastAPI dependency that asserts the user has the given permission.

    Returns a ``CallerContext`` instead of ``CurrentUserDTO`` so that
    downstream services receive a context object with ``has_permission``
    and ``require_permission`` helpers.

    Usage::

        @router.get("/items")
        async def list_items(
            ctx: CallerContext = Depends(require_permission("items.read")),
        ): ...
    """

    async def _check(
        user: CurrentUserDTO = Depends(get_current_user),
    ) -> CallerContext:
        if permission not in user.permissions:
            raise ForbiddenError(permission)
        return CallerContext(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            permissions=frozenset(user.permissions),
        )

    return _check
