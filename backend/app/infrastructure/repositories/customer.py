"""Customer repository for customer management context."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.customer import CustomerModel
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyCustomerRepository(BaseRepository[CustomerModel]):
    """Data-access layer for customer persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CustomerModel)

    @staticmethod
    def _escape_like_pattern(pattern: str) -> str:
        """Escape special LIKE/ILIKE characters to prevent wildcard injection."""
        return pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def search(self, query: str, pagination: Pagination) -> PaginatedResult[CustomerModel]:
        """Search customers by company name (case-insensitive partial match).

        If the query string is empty, returns all customers (paginated).
        Always excludes soft-deleted rows.
        """
        stmt = select(CustomerModel)
        stmt = self._apply_soft_delete_filter(stmt)
        if query:
            escaped = self._escape_like_pattern(query)
            stmt = stmt.where(CustomerModel.company_name.ilike(f"%{escaped}%"))
        return await self._paginate(stmt, pagination)

    async def get_detail(self, customer_id: UUID) -> CustomerModel | None:
        """Fetch a single customer by ID with eager-loaded source relationship.

        Returns None if the customer does not exist or is soft-deleted.
        """
        stmt = (
            select(CustomerModel)
            .options(selectinload(CustomerModel.source))
            .where(
                CustomerModel.id == customer_id,
                CustomerModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
