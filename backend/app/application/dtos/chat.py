"""DTOs for the conversational agent context."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ToolCallAttribution:
    """Metadata about a tool call made during agent processing."""

    tool: str
    input: dict
    result_count: int | None = None


@dataclass(frozen=True)
class SourceAttribution:
    """A single source attribution entry referencing actual data records used."""

    table: str
    record_id: str
    fields_used: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponseDTO:
    """Result of processing a chat message through the orchestrator agent."""

    session_id: UUID
    role: str = "assistant"
    message: str = ""
    sources: list[SourceAttribution] = field(default_factory=list)
    tool_calls: list[ToolCallAttribution] = field(default_factory=list)
