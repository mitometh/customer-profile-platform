"""User management service for identity & access context."""

from uuid import UUID

from app.application.dtos.auth import UserSummaryDTO
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.user import UserModel
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository
from app.infrastructure.repositories.user import SqlAlchemyUserRepository
from app.infrastructure.security import hash_password


class UserService:
    """CRUD operations for user management. Gate 2 permission checks at top of every method."""

    def __init__(
        self,
        user_repo: SqlAlchemyUserRepository,
        role_repo: SqlAlchemyRoleRepository,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def create_user(
        self,
        email: str,
        full_name: str,
        role: str,
        password: str,
        permissions: list[str],
    ) -> UserSummaryDTO:
        """Create a new user.

        Gate 2: requires 'users.manage' permission.

        Raises:
            ForbiddenError: If the caller lacks users.manage.
            ValidationError: If the role does not exist.
            ConflictError: If the email is already in use.
        """
        # Gate 2
        if "users.manage" not in permissions:
            raise ForbiddenError("users.manage")

        # Validate role exists
        role_obj = await self._role_repo.get_by_name(role)
        if role_obj is None:
            raise ValidationError(f"Role '{role}' does not exist")

        # Check email uniqueness
        if await self._user_repo.email_exists(email):
            raise ConflictError(f"Email '{email}' is already in use")

        # Hash password and create user
        user = UserModel(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role_id=role_obj.id,
            is_active=True,
        )
        user = await self._user_repo.create(user)

        return self._to_summary_dto(user, role)

    async def update_user(
        self,
        user_id: UUID,
        updates: dict,
        permissions: list[str],
        current_user_id: UUID,
    ) -> UserSummaryDTO:
        """Partially update a user (role, is_active, full_name).

        Gate 2: requires 'users.manage' permission.

        Raises:
            ForbiddenError: If the caller lacks users.manage.
            NotFoundError: If the target user does not exist.
            ValidationError: If the role does not exist or deactivating the last admin.
        """
        # Gate 2
        if "users.manage" not in permissions:
            raise ForbiddenError("users.manage")

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User", user_id)

        role_name: str | None = None

        # Apply partial updates
        if "role_id" in updates and updates["role_id"] is not None:
            role = await self._role_repo.get_by_id(updates["role_id"])
            if role is None:
                raise ValidationError(f"Role with id '{updates['role_id']}' does not exist")
            user.role_id = role.id
            role_name = role.name

        if "full_name" in updates and updates["full_name"] is not None:
            user.full_name = updates["full_name"]

        if "is_active" in updates and updates["is_active"] is not None:
            # If deactivating, check not last active admin
            if not updates["is_active"]:
                await self._check_not_last_admin(user)
            user.is_active = updates["is_active"]

        user = await self._user_repo.update(user)

        # Resolve role name if not already set by the update
        if role_name is None:
            role = await self._role_repo.get_by_id(user.role_id)
            role_name = role.name if role else "unknown"

        return self._to_summary_dto(user, role_name)

    async def list_users(
        self,
        pagination: Pagination,
        permissions: list[str],
    ) -> PaginatedResult[UserSummaryDTO]:
        """Return a paginated list of users.

        Gate 2: requires 'users.read' permission.

        Raises:
            ForbiddenError: If the caller lacks users.read.
        """
        # Gate 2
        if "users.read" not in permissions:
            raise ForbiddenError("users.read")

        result = await self._user_repo.list_users(pagination)

        # Map models to DTOs
        dto_data: list[UserSummaryDTO] = []
        for user in result.data:
            role = await self._role_repo.get_by_id(user.role_id)
            role_name = role.name if role else "unknown"
            dto_data.append(self._to_summary_dto(user, role_name))

        return PaginatedResult(
            data=dto_data,
            total=result.total,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary_dto(user: UserModel, role_name: str) -> UserSummaryDTO:
        """Map a UserModel and its role name to a UserSummaryDTO."""
        return UserSummaryDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=role_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )

    async def _check_not_last_admin(self, user: UserModel) -> None:
        """Raise ValidationError if deactivating the user would leave zero active admins."""
        admin_role = await self._role_repo.get_by_name("admin")
        if admin_role is None:
            return

        # Only matters if the user being deactivated is an admin
        if user.role_id != admin_role.id:
            return

        # Count active admins (other than this user)
        from sqlalchemy import func, select

        stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.role_id == admin_role.id,
                UserModel.is_active.is_(True),
                UserModel.deleted_at.is_(None),
                UserModel.id != user.id,
            )
        )
        result = await self._user_repo._session.execute(stmt)
        active_admin_count = result.scalar() or 0

        if active_admin_count == 0:
            raise ValidationError("Cannot deactivate the last active admin user")
