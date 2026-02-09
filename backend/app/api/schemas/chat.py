"""Pydantic schemas for the chat API endpoint."""

from datetime import datetime
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


# --- Conversation history schemas ---


class SessionSummarySchema(BaseModel):
    """Summary of a chat session for the session list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    message_count: int
    last_message_at: datetime | None = None
    created_at: datetime


class SessionMessageSchema(BaseModel):
    """A single message within a session detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    sources: list[SourceAttributionSchema] = []
    tool_calls: list[ToolCallSchema] = []
    created_at: datetime


class SessionDetailSchema(BaseModel):
    """Full session with all messages."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    message_count: int
    last_message_at: datetime | None = None
    created_at: datetime
    messages: list[SessionMessageSchema] = []
