"""DTOs for the customer management and activity tracking contexts."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class EventSummaryDTO:
    """Compact event representation for timelines and embedded lists."""

    id: UUID
    customer_id: UUID | None
    event_type: str
    title: str
    description: str | None
    occurred_at: datetime
    source_name: str | None
    data: dict | None


@dataclass(frozen=True)
class CustomerSummaryDTO:
    """Compact customer representation for list views and search results."""

    id: UUID
    company_name: str
    contact_name: str | None
    email: str | None
    contract_value: Decimal | None
    currency_code: str
    signup_date: date | None
    source_name: str | None


@dataclass(frozen=True)
class CustomerDetailDTO:
    """Full customer 360 view: profile + recent events + metrics."""

    id: UUID
    company_name: str
    contact_name: str | None
    email: str | None
    phone: str | None
    industry: str | None
    contract_value: Decimal | None
    currency_code: str
    signup_date: date | None
    source_name: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    recent_events: list[EventSummaryDTO] = field(default_factory=list)
    metrics: list[dict] = field(default_factory=list)
