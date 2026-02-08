from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import PaginatedResult, Pagination, decode_cursor, encode_cursor

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository providing CRUD, soft-delete, and cursor pagination.

    Subclasses specify the SQLAlchemy model class. All queries automatically
    exclude soft-deleted rows (where deleted_at IS NOT NULL).
    """

    def __init__(self, session: AsyncSession, model_class: type[T]) -> None:
        self._session = session
        self._model_class = model_class

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, entity_id: UUID) -> T | None:
        """Fetch a single entity by primary key, excluding soft-deleted rows."""
        stmt = select(self._model_class).where(
            self._model_class.id == entity_id,  # type: ignore[attr-defined]
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, pagination: Pagination) -> PaginatedResult[T]:
        """Return a paginated list of entities ordered by created_at DESC, id DESC."""
        stmt = select(self._model_class)
        stmt = self._apply_soft_delete_filter(stmt)
        return await self._paginate(stmt, pagination)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, entity: T) -> T:
        """Add a new entity to the session and flush to obtain server defaults."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Merge changes for an existing entity and flush."""
        merged = await self._session.merge(entity)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def soft_delete(
        self,
        entity_id: UUID,
        deleted_by: UUID | None = None,
    ) -> None:
        """Mark an entity as soft-deleted by setting deleted_at (and optionally deleted_by)."""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return
        entity.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        if deleted_by is not None:
            entity.deleted_by = deleted_by  # type: ignore[attr-defined]
        await self._session.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_soft_delete_filter(self, stmt: Select) -> Select:
        """Append a WHERE clause excluding soft-deleted rows.

        Only applied when the model has a ``deleted_at`` column
        (i.e. uses SoftDeleteMixin).
        """
        if hasattr(self._model_class, "deleted_at"):
            stmt = stmt.where(
                self._model_class.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        return stmt

    async def _paginate(
        self,
        stmt: Select,
        pagination: Pagination,
    ) -> PaginatedResult[T]:
        """Apply cursor-based keyset pagination to an existing SELECT.

        Cursor encoding: base64(json({"id": "...", "created_at": "..."}))

        Logic:
        1. Decode cursor -> (created_at, id) for keyset seek.
        2. WHERE (created_at, id) < (cursor_ts, cursor_id) for DESC ordering.
        3. ORDER BY created_at DESC, id DESC.
        4. Fetch limit + 1 rows to determine has_next.
        5. Encode next_cursor from the last returned item.
        """
        model = self._model_class

        # Apply cursor seek
        if pagination.cursor is not None:
            cursor_data = decode_cursor(pagination.cursor)
            stmt = stmt.where(
                tuple_(
                    model.created_at,  # type: ignore[attr-defined]
                    model.id,  # type: ignore[attr-defined]
                )
                < tuple_(
                    cursor_data["created_at"],
                    cursor_data["id"],
                ),
            )

        # Ordering
        stmt = stmt.order_by(
            model.created_at.desc(),  # type: ignore[attr-defined]
            model.id.desc(),  # type: ignore[attr-defined]
        )

        # Fetch one extra to determine if more rows exist
        stmt = stmt.limit(pagination.limit + 1)

        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_next = len(rows) > pagination.limit
        if has_next:
            rows = rows[: pagination.limit]

        next_cursor: str | None = None
        if has_next and rows:
            last = rows[-1]
            next_cursor = encode_cursor(
                last.id,  # type: ignore[attr-defined]
                last.created_at,  # type: ignore[attr-defined]
            )

        return PaginatedResult(
            data=rows,
            total=None,
            has_next=has_next,
            next_cursor=next_cursor,
        )
