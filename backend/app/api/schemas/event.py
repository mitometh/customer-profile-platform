"""Pydantic schemas for activity tracking context."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventSummarySchema(BaseModel):
    """Compact event representation for timelines and embedded lists."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID | None = None
    event_type: str
    title: str
    description: str | None = None
    occurred_at: datetime
    source_name: str | None = None
    data: dict | None = None


class EventFilterParams(BaseModel):
    """Query parameters for filtering events."""

    event_type: str | None = None
    since: datetime | None = None
    until: datetime | None = None
