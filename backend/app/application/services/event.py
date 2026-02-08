"""Event service for activity tracking context."""

from datetime import datetime
from uuid import UUID

from app.application.dtos.customer import EventSummaryDTO
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.event import EventModel
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.event import SqlAlchemyEventRepository


class EventService:
    """Use-case orchestration for event timeline queries. Gate 2 permission checks at top of every method."""

    def __init__(
        self,
        event_repo: SqlAlchemyEventRepository,
        customer_repo: SqlAlchemyCustomerRepository,
    ) -> None:
        self._event_repo = event_repo
        self._customer_repo = customer_repo

    async def list_events(
        self,
        customer_id: UUID,
        event_type: str | None,
        since: datetime | None,
        until: datetime | None,
        order: str = "desc",
        pagination: Pagination = Pagination(),
        permissions: list[str] | None = None,
    ) -> PaginatedResult[EventSummaryDTO]:
        """Return a paginated timeline of events for a customer.

        Gate 2: requires 'events.read' permission.

        Raises:
            ForbiddenError: If the caller lacks events.read.
            NotFoundError: If the customer does not exist or is soft-deleted.
        """
        # Gate 2
        if permissions is None or "events.read" not in permissions:
            raise ForbiddenError("events.read")

        # Verify customer exists
        customer = await self._customer_repo.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)

        result = await self._event_repo.list_for_customer(
            customer_id=customer_id,
            event_type=event_type,
            since=since,
            until=until,
            order=order,
            pagination=pagination,
        )

        dto_data = [self._to_event_dto(e) for e in result.data]

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
    def _to_event_dto(event: EventModel) -> EventSummaryDTO:
        """Map an EventModel to an EventSummaryDTO."""
        source_name: str | None = None
        if event.source is not None:
            source_name = event.source.name

        return EventSummaryDTO(
            id=event.id,
            customer_id=event.customer_id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            occurred_at=event.occurred_at,
            source_name=source_name,
            data=event.data,
        )
