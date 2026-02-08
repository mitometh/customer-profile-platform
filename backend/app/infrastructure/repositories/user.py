"""User repository for identity & access context."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.user import UserModel
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyUserRepository(BaseRepository[UserModel]):
    """Data-access layer for user persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserModel)

    async def get_by_email(self, email: str) -> UserModel | None:
        """Fetch a user by email, excluding soft-deleted rows."""
        stmt = select(UserModel).where(UserModel.email == email)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, pagination: Pagination) -> PaginatedResult[UserModel]:
        """Return a paginated list of non-deleted users."""
        stmt = select(UserModel)
        stmt = self._apply_soft_delete_filter(stmt)
        return await self._paginate(stmt, pagination)

    async def email_exists(self, email: str) -> bool:
        """Check whether an email is already in use (non-deleted user)."""
        stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.email == email,
                UserModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0
