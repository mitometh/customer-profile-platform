"""Customer service for customer management context."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.application.dtos.customer import (
    CustomerDetailDTO,
    CustomerSummaryDTO,
    EventSummaryDTO,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.customer import CustomerModel
from app.infrastructure.models.event import EventModel
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.event import SqlAlchemyEventRepository


class CustomerService:
    """Use-case orchestration for customer queries. Gate 2 permission checks at top of every method."""

    def __init__(
        self,
        customer_repo: SqlAlchemyCustomerRepository,
        event_repo: SqlAlchemyEventRepository,
    ) -> None:
        self._customer_repo = customer_repo
        self._event_repo = event_repo

    async def list_customers(
        self,
        search: str | None,
        pagination: Pagination,
        permissions: list[str],
    ) -> PaginatedResult[CustomerSummaryDTO]:
        """Return a paginated list of customers, optionally filtered by search query.

        Gate 2: requires 'customers.read' permission.

        Raises:
            ForbiddenError: If the caller lacks customers.read.
        """
        # Gate 2
        if "customers.read" not in permissions:
            raise ForbiddenError("customers.read")

        if search:
            result = await self._customer_repo.search(search, pagination)
        else:
            result = await self._customer_repo.list(pagination)

        dto_data = [self._to_summary_dto(c) for c in result.data]

        return PaginatedResult(
            data=dto_data,
            total=result.total,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        )

    async def get_customer_detail(
        self,
        customer_id: UUID,
        permissions: list[str],
    ) -> CustomerDetailDTO:
        """Return a full customer 360 view with recent events.

        Gate 2: requires 'customers.read' permission.

        Raises:
            ForbiddenError: If the caller lacks customers.read.
            NotFoundError: If the customer does not exist or is soft-deleted.
        """
        # Gate 2
        if "customers.read" not in permissions:
            raise ForbiddenError("customers.read")

        customer = await self._customer_repo.get_detail(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)

        # Get recent events (last 10)
        recent_events = await self._event_repo.get_recent_for_customer(customer_id, limit=10)
        event_dtos = [self._to_event_dto(e) for e in recent_events]

        source_name: str | None = None
        if customer.source is not None:
            source_name = customer.source.name

        return CustomerDetailDTO(
            id=customer.id,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            phone=customer.phone,
            industry=customer.industry,
            contract_value=customer.contract_value,
            currency_code=customer.currency_code,
            signup_date=customer.signup_date,
            source_name=source_name,
            notes=customer.notes,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            recent_events=event_dtos,
            metrics=[],  # Populated by metrics service later
        )

    async def create_customer(
        self,
        company_name: str,
        permissions: list[str],
        current_user_id: UUID,
        contact_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        industry: str | None = None,
        contract_value: Decimal | None = None,
        currency_code: str = "USD",
        signup_date: date | None = None,
        notes: str | None = None,
    ) -> CustomerDetailDTO:
        """Create a new customer.

        Gate 2: requires 'customers.manage' permission.

        Raises:
            ForbiddenError: If the caller lacks customers.manage.
        """
        # Gate 2
        if "customers.manage" not in permissions:
            raise ForbiddenError("customers.manage")

        customer = CustomerModel(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            industry=industry,
            contract_value=contract_value,
            currency_code=currency_code,
            signup_date=signup_date,
            notes=notes,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        customer = await self._customer_repo.create(customer)

        return CustomerDetailDTO(
            id=customer.id,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            phone=customer.phone,
            industry=customer.industry,
            contract_value=customer.contract_value,
            currency_code=customer.currency_code,
            signup_date=customer.signup_date,
            source_name=None,
            notes=customer.notes,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            recent_events=[],
            metrics=[],
        )

    async def update_customer(
        self,
        customer_id: UUID,
        updates: dict,
        permissions: list[str],
        current_user_id: UUID,
    ) -> CustomerDetailDTO:
        """Partially update a customer.

        Gate 2: requires 'customers.manage' permission.

        Raises:
            ForbiddenError: If the caller lacks customers.manage.
            NotFoundError: If the customer does not exist or is soft-deleted.
        """
        # Gate 2
        if "customers.manage" not in permissions:
            raise ForbiddenError("customers.manage")

        customer = await self._customer_repo.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)

        # Apply partial updates
        updatable_fields = [
            "company_name",
            "contact_name",
            "email",
            "phone",
            "industry",
            "contract_value",
            "currency_code",
            "signup_date",
            "notes",
        ]
        for field in updatable_fields:
            if field in updates and updates[field] is not None:
                setattr(customer, field, updates[field])

        customer.updated_by = current_user_id
        customer = await self._customer_repo.update(customer)

        source_name: str | None = None
        if customer.source is not None:
            source_name = customer.source.name

        # Get recent events
        recent_events = await self._event_repo.get_recent_for_customer(customer_id, limit=10)
        event_dtos = [self._to_event_dto(e) for e in recent_events]

        return CustomerDetailDTO(
            id=customer.id,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            phone=customer.phone,
            industry=customer.industry,
            contract_value=customer.contract_value,
            currency_code=customer.currency_code,
            signup_date=customer.signup_date,
            source_name=source_name,
            notes=customer.notes,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            recent_events=event_dtos,
            metrics=[],
        )

    async def delete_customer(
        self,
        customer_id: UUID,
        permissions: list[str],
        current_user_id: UUID,
    ) -> None:
        """Soft-delete a customer.

        Gate 2: requires 'customers.manage' permission.

        Raises:
            ForbiddenError: If the caller lacks customers.manage.
            NotFoundError: If the customer does not exist or is already soft-deleted.
        """
        # Gate 2
        if "customers.manage" not in permissions:
            raise ForbiddenError("customers.manage")

        customer = await self._customer_repo.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)

        await self._customer_repo.soft_delete(customer_id, deleted_by=current_user_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary_dto(customer: CustomerModel) -> CustomerSummaryDTO:
        """Map a CustomerModel to a CustomerSummaryDTO."""
        source_name: str | None = None
        if customer.source is not None:
            source_name = customer.source.name

        return CustomerSummaryDTO(
            id=customer.id,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            contract_value=customer.contract_value,
            currency_code=customer.currency_code,
            signup_date=customer.signup_date,
            source_name=source_name,
        )

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
