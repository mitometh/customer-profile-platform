"""Pydantic schemas for customer management context."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.event import EventSummarySchema


class CustomerSummarySchema(BaseModel):
    """Compact customer representation for list views and search results."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    contact_name: str | None = None
    email: str | None = None
    contract_value: Decimal | None = None
    currency_code: str = "USD"
    signup_date: date | None = None
    source_name: str | None = None


class CustomerCreateRequest(BaseModel):
    """POST /api/customers request body."""

    model_config = ConfigDict(from_attributes=True)

    company_name: str = Field(..., max_length=255)
    contact_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)
    contract_value: Decimal | None = None
    currency_code: str = Field("USD", max_length=3)
    signup_date: date | None = None
    notes: str | None = None


class CustomerUpdateRequest(BaseModel):
    """PATCH /api/customers/{id} request body."""

    model_config = ConfigDict(from_attributes=True)

    company_name: str | None = Field(None, max_length=255)
    contact_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)
    contract_value: Decimal | None = None
    currency_code: str | None = Field(None, max_length=3)
    signup_date: date | None = None
    notes: str | None = None


class CustomerDetailSchema(BaseModel):
    """Full customer 360 view: profile + recent events + metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    industry: str | None = None
    contract_value: Decimal | None = None
    currency_code: str = "USD"
    signup_date: date | None = None
    source_name: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    recent_events: list[EventSummarySchema] = []
    metrics: list[dict] = []
