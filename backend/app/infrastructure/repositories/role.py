"""Role repository for identity & access context."""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.role import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)
from app.infrastructure.models.user import UserModel
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyRoleRepository(BaseRepository[RoleModel]):
    """Data-access layer for roles and role-permission lookups."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RoleModel)

    async def get_by_name(self, name: str) -> RoleModel | None:
        """Fetch a role by its unique name, excluding soft-deleted rows."""
        stmt = select(RoleModel).where(RoleModel.name == name)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_permissions_for_role(self, role_id: UUID) -> list[str]:
        """Return the list of permission code strings for a given role.

        Queries the role_permissions junction table joined with permissions.
        No Redis caching — kept simple for now.
        """
        stmt = (
            select(PermissionModel.code)
            .join(
                RolePermissionModel,
                PermissionModel.id == RolePermissionModel.permission_id,
            )
            .where(RolePermissionModel.role_id == role_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[RoleModel]:
        """Return all non-deleted roles."""
        stmt = select(RoleModel)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_roles(self, pagination: Pagination) -> PaginatedResult[RoleModel]:
        """Return a paginated list of non-deleted roles."""
        stmt = select(RoleModel)
        stmt = self._apply_soft_delete_filter(stmt)
        return await self._paginate(stmt, pagination)

    async def name_exists(self, name: str, exclude_id: UUID | None = None) -> bool:
        """Check if a role name already exists (excluding soft-deleted and optionally a specific role)."""
        stmt = select(func.count()).select_from(RoleModel).where(RoleModel.name == name)
        stmt = self._apply_soft_delete_filter(stmt)
        if exclude_id is not None:
            stmt = stmt.where(RoleModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def get_user_count(self, role_id: UUID) -> int:
        """Count active (non-deleted) users assigned to a role."""
        stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.role_id == role_id,
                UserModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_all_permissions(self) -> list[PermissionModel]:
        """Return all permissions (seed-only, no soft-delete)."""
        stmt = select(PermissionModel).order_by(PermissionModel.code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_permissions_by_ids(self, permission_ids: list[UUID]) -> list[PermissionModel]:
        """Return permissions matching the given IDs."""
        if not permission_ids:
            return []
        stmt = select(PermissionModel).where(PermissionModel.id.in_(permission_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_permission_models_for_role(self, role_id: UUID) -> list[PermissionModel]:
        """Return full permission models for a role (not just codes)."""
        stmt = (
            select(PermissionModel)
            .join(
                RolePermissionModel,
                PermissionModel.id == RolePermissionModel.permission_id,
            )
            .where(RolePermissionModel.role_id == role_id)
            .order_by(PermissionModel.code)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def replace_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """Replace all role-permission mappings for a role (transactional)."""
        # Delete existing mappings
        await self._session.execute(delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id))
        # Insert new mappings
        for perm_id in permission_ids:
            self._session.add(RolePermissionModel(role_id=role_id, permission_id=perm_id))
        await self._session.flush()
