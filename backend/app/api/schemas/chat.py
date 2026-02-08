"""Pydantic schemas for the chat API endpoint."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""

    message: str = Field(..., min_length=1, max_length=2000, description="Natural language message")
    session_id: UUID | None = Field(
        None,
        description="Omit for new session; include to continue an existing conversation",
    )


class MessageSchema(BaseModel):
    """A single assistant message with role and content."""

    role: str = "assistant"
    content: str


class ToolCallSchema(BaseModel):
    """Tool call metadata showing which tool was invoked and its input."""

    model_config = ConfigDict(from_attributes=True)

    tool: str
    input: dict
    result_count: int | None = None


class SourceAttributionSchema(BaseModel):
    """Source attribution entry referencing actual data records used."""

    model_config = ConfigDict(from_attributes=True)

    table: str
    record_id: str
    fields_used: dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Response body for POST /api/chat."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    message: MessageSchema
    sources: list[SourceAttributionSchema] = []
    tool_calls: list[ToolCallSchema] = []
