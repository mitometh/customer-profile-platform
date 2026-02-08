"""Pydantic schemas for source management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceSummarySchema(BaseModel):
    """Source summary for list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime


class SourceDetailSchema(BaseModel):
    """Full source detail (excludes api_token_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SourceCreateRequest(BaseModel):
    """POST /api/sources request body."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class SourceCreateResponse(BaseModel):
    """POST /api/sources response — includes raw api_token (shown only at creation)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    api_token: str
    is_active: bool
    created_at: datetime


class SourceUpdateRequest(BaseModel):
    """PATCH /api/sources/{source_id} request body."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=100)
    description: str | None = None
    is_active: bool | None = None
