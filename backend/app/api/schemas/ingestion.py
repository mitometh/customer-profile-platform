"""Pydantic schemas for the ingestion webhook endpoint."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class IngestRequest(BaseModel):
    """POST /hooks/ingest request body."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str
    customer_identifier: str
    title: str
    description: str | None = None
    occurred_at: datetime
    data: dict[str, Any] | None = None


class IngestResponse(BaseModel):
    """POST /hooks/ingest 202 Accepted response body."""

    status: str = "accepted"
    event_id: str
