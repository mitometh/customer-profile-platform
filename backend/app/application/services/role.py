"""Role & permission management service for identity & access context."""

from uuid import UUID

from app.application.dtos.role import PermissionDTO, RoleDetailDTO, RoleSummaryDTO
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.role import RoleModel
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository


class RoleService:
    """CRUD operations for role management. Gate 2 permission checks at top of every method."""

    def __init__(self, role_repo: SqlAlchemyRoleRepository) -> None:
        self._role_repo = role_repo

    # ------------------------------------------------------------------
    # Permissions (read-only)
    # ------------------------------------------------------------------

    async def list_permissions(
        self,
        permissions: list[str],
    ) -> list[PermissionDTO]:
        """List all available permissions.

        Gate 2: requires 'roles.read' permission.
        """
        if "roles.read" not in permissions:
            raise ForbiddenError("roles.read")

        perm_models = await self._role_repo.get_all_permissions()
        return [PermissionDTO(id=p.id, code=p.code, description=p.description) for p in perm_models]

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------

    async def list_roles(
        self,
        pagination: Pagination,
        permissions: list[str],
    ) -> PaginatedResult[RoleSummaryDTO]:
        """List all roles with permission counts.

        Gate 2: requires 'roles.read' permission.
        """
        if "roles.read" not in permissions:
            raise ForbiddenError("roles.read")

        result = await self._role_repo.list_roles(pagination)

        dto_data: list[RoleSummaryDTO] = []
        for role in result.data:
            perm_count = len(role.permissions)  # selectin-loaded
            dto_data.append(self._to_summary_dto(role, perm_count))

        return PaginatedResult(
            data=dto_data,
            total=result.total,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        )

    async def get_role(
        self,
        role_id: UUID,
        permissions: list[str],
    ) -> RoleDetailDTO:
        """Get role detail with full permission list and user count.

        Gate 2: requires 'roles.read' permission.
        """
        if "roles.read" not in permissions:
            raise ForbiddenError("roles.read")

        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError("Role", role_id)

        return await self._to_detail_dto(role)

    async def create_role(
        self,
        name: str,
        display_name: str,
        description: str | None,
        permission_ids: list[UUID],
        permissions: list[str],
    ) -> RoleDetailDTO:
        """Create a new custom role with specified permissions.

        Gate 2: requires 'roles.manage' permission.

        Raises:
            ForbiddenError: Caller lacks roles.manage.
            ConflictError: Role name already exists.
            ValidationError: Invalid permission IDs.
        """
        if "roles.manage" not in permissions:
            raise ForbiddenError("roles.manage")

        # Check name uniqueness
        if await self._role_repo.name_exists(name):
            raise ConflictError(f"Role name '{name}' already exists")

        # Validate all permission IDs exist
        await self._validate_permission_ids(permission_ids)

        # Create the role
        role = RoleModel(
            name=name,
            display_name=display_name,
            description=description,
            is_system=False,
        )
        role = await self._role_repo.create(role)

        # Assign permissions
        await self._role_repo.replace_role_permissions(role.id, permission_ids)

        # Reload to get fresh relationships
        role = await self._role_repo.get_by_id(role.id)
        return await self._to_detail_dto(role)

    async def update_role(
        self,
        role_id: UUID,
        updates: dict,
        permissions: list[str],
    ) -> RoleDetailDTO:
        """Update role details and/or permission assignments.

        Gate 2: requires 'roles.manage' permission.

        Raises:
            ForbiddenError: Caller lacks roles.manage.
            NotFoundError: Role not found.
            ValidationError: Invalid permission IDs or empty permission set.
        """
        if "roles.manage" not in permissions:
            raise ForbiddenError("roles.manage")

        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError("Role", role_id)

        # Apply scalar updates
        if "display_name" in updates and updates["display_name"] is not None:
            role.display_name = updates["display_name"]
        if "description" in updates:
            role.description = updates["description"]

        role = await self._role_repo.update(role)

        # Replace permissions if provided
        if "permissions" in updates and updates["permissions"] is not None:
            permission_ids: list[UUID] = updates["permissions"]
            await self._validate_permission_ids(permission_ids)
            await self._role_repo.replace_role_permissions(role.id, permission_ids)

        # Reload to get fresh relationships
        role = await self._role_repo.get_by_id(role.id)
        return await self._to_detail_dto(role)

    async def delete_role(
        self,
        role_id: UUID,
        permissions: list[str],
        deleted_by: UUID,
    ) -> None:
        """Soft-delete a custom role.

        Gate 2: requires 'roles.manage' permission.

        Raises:
            ForbiddenError: Caller lacks roles.manage.
            NotFoundError: Role not found.
            ValidationError: System role or role with assigned users.
        """
        if "roles.manage" not in permissions:
            raise ForbiddenError("roles.manage")

        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError("Role", role_id)

        if role.is_system:
            raise ValidationError(
                f"Cannot delete system role '{role.name}'. System roles can be updated but not deleted."
            )

        user_count = await self._role_repo.get_user_count(role_id)
        if user_count > 0:
            raise ValidationError(
                f"Cannot delete role '{role.name}': {user_count} user(s) are still assigned. "
                "Reassign users to another role before deleting."
            )

        await self._role_repo.soft_delete(role_id, deleted_by=deleted_by)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary_dto(role: RoleModel, permission_count: int) -> RoleSummaryDTO:
        return RoleSummaryDTO(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_system=role.is_system,
            permission_count=permission_count,
            created_at=role.created_at,
        )

    async def _to_detail_dto(self, role: RoleModel) -> RoleDetailDTO:
        perm_models = await self._role_repo.get_permission_models_for_role(role.id)
        user_count = await self._role_repo.get_user_count(role.id)
        return RoleDetailDTO(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_system=role.is_system,
            permissions=[PermissionDTO(id=p.id, code=p.code, description=p.description) for p in perm_models],
            user_count=user_count,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    async def _validate_permission_ids(self, permission_ids: list[UUID]) -> None:
        """Validate that all provided permission IDs exist."""
        found = await self._role_repo.get_permissions_by_ids(permission_ids)
        found_ids = {p.id for p in found}
        missing = [pid for pid in permission_ids if pid not in found_ids]
        if missing:
            raise ValidationError(f"Invalid permission IDs: {[str(m) for m in missing]}")
