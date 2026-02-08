"""Authentication service for identity & access context."""

from datetime import UTC, datetime
from uuid import UUID

from app.api.dependencies import CurrentUserDTO
from app.application.dtos.auth import LoginResultDTO
from app.core.exceptions import UnauthorizedError
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository
from app.infrastructure.repositories.user import SqlAlchemyUserRepository
from app.infrastructure.security import create_access_token, hash_password, verify_password


class AuthService:
    """Handles login authentication and current-user resolution."""

    def __init__(
        self,
        user_repo: SqlAlchemyUserRepository,
        role_repo: SqlAlchemyRoleRepository,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def login(self, email: str, password: str) -> LoginResultDTO:
        """Authenticate a user by email and password, returning a JWT.

        Uses a single generic error message for both not-found and wrong-password
        cases to prevent user enumeration.

        Raises:
            UnauthorizedError: If the credentials are invalid or the account is
                not active / soft-deleted.
        """
        user = await self._user_repo.get_by_email(email)

        # Always perform password verification to prevent timing attacks.
        # Use a dummy hash when user is not found so the response time is
        # indistinguishable from a wrong-password attempt.
        _dummy_hash = hash_password("dummy-timing-pad")
        password_hash = user.password_hash if user else _dummy_hash
        is_valid = verify_password(password, password_hash)

        if user is None or not is_valid or not user.is_active:
            raise UnauthorizedError("Invalid credentials")

        # Load role name and permissions
        role = await self._role_repo.get_by_id(user.role_id)
        role_name = role.name if role else "unknown"
        permissions = await self._role_repo.get_permissions_for_role(user.role_id)

        # Create JWT
        access_token = create_access_token(data={"sub": str(user.id)})

        # Update last_login_at
        user.last_login_at = datetime.now(UTC)
        await self._user_repo.update(user)

        current_user = CurrentUserDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=role_name,
            permissions=permissions,
        )

        return LoginResultDTO(
            access_token=access_token,
            token_type="bearer",
            user=current_user,
        )

    async def get_current_user_dto(self, user_id: UUID) -> CurrentUserDTO:
        """Load a user with role and permissions by user ID.

        Raises:
            UnauthorizedError: If the user is not found, soft-deleted, or inactive.
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        if not user.is_active:
            raise UnauthorizedError("User account is deactivated")

        role = await self._role_repo.get_by_id(user.role_id)
        role_name = role.name if role else "unknown"
        permissions = await self._role_repo.get_permissions_for_role(user.role_id)

        return CurrentUserDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=role_name,
            permissions=permissions,
        )
