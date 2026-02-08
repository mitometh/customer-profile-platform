"""Event repository for activity tracking context."""

import base64
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.event import EventModel
from app.infrastructure.repositories.base import BaseRepository


def _encode_event_cursor(entity_id: UUID, occurred_at: datetime) -> str:
    """Encode a keyset cursor for event pagination using (occurred_at, id)."""
    payload = {
        "id": str(entity_id),
        "occurred_at": occurred_at.isoformat(),
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_event_cursor(cursor: str) -> dict:
    """Decode a base64 event cursor into a dict with 'id' and 'occurred_at'.

    Raises ValueError if the cursor is malformed.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw)
        return {
            "id": UUID(data["id"]),
            "occurred_at": datetime.fromisoformat(data["occurred_at"]),
        }
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid event cursor: {cursor}") from exc


class SqlAlchemyEventRepository(BaseRepository[EventModel]):
    """Data-access layer for event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventModel)

    async def list_for_customer(
        self,
        customer_id: UUID,
        event_type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        order: str = "desc",
        pagination: Pagination = Pagination(),
    ) -> PaginatedResult[EventModel]:
        """Return paginated events for a customer with optional filters.

        Uses (occurred_at, id) for cursor pagination instead of (created_at, id).
        Orders by occurred_at DESC, id DESC.
        """
        stmt = select(EventModel).where(EventModel.customer_id == customer_id)
        stmt = self._apply_soft_delete_filter(stmt)

        # Optional filters
        if event_type is not None:
            stmt = stmt.where(EventModel.event_type == event_type)
        if since is not None:
            stmt = stmt.where(EventModel.occurred_at >= since)
        if until is not None:
            stmt = stmt.where(EventModel.occurred_at <= until)

        # Cursor-based pagination using (occurred_at, id)
        return await self._paginate_by_occurred_at(stmt, pagination, order=order)

    async def get_recent_for_customer(self, customer_id: UUID, limit: int = 10) -> list[EventModel]:
        """Get the most recent events for a customer detail view.

        Returns up to ``limit`` events ordered by occurred_at DESC.
        """
        stmt = (
            select(EventModel)
            .where(EventModel.customer_id == customer_id)
            .order_by(EventModel.occurred_at.desc(), EventModel.id.desc())
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _paginate_by_occurred_at(
        self,
        stmt: select,
        pagination: Pagination,
        order: str = "desc",
    ) -> PaginatedResult[EventModel]:
        """Apply cursor-based keyset pagination using (occurred_at, id).

        Same logic as BaseRepository._paginate but keyed on occurred_at
        instead of created_at.
        """
        model = EventModel

        # Apply cursor seek
        if pagination.cursor is not None:
            cursor_data = _decode_event_cursor(pagination.cursor)
            if order == "asc":
                stmt = stmt.where(
                    tuple_(
                        model.occurred_at,
                        model.id,
                    )
                    > tuple_(
                        cursor_data["occurred_at"],
                        cursor_data["id"],
                    ),
                )
            else:
                stmt = stmt.where(
                    tuple_(
                        model.occurred_at,
                        model.id,
                    )
                    < tuple_(
                        cursor_data["occurred_at"],
                        cursor_data["id"],
                    ),
                )

        # Ordering
        if order == "asc":
            stmt = stmt.order_by(
                model.occurred_at.asc(),
                model.id.asc(),
            )
        else:
            stmt = stmt.order_by(
                model.occurred_at.desc(),
                model.id.desc(),
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
            next_cursor = _encode_event_cursor(last.id, last.occurred_at)

        return PaginatedResult(
            data=rows,
            total=None,
            has_next=has_next,
            next_cursor=next_cursor,
        )
