import base64
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class MetricValueType(StrEnum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    PERCENTAGE = "percentage"


# ---------------------------------------------------------------------------
# Cursor helpers
# ---------------------------------------------------------------------------


def encode_cursor(entity_id: UUID, created_at: datetime) -> str:
    """Encode a keyset cursor as base64-encoded JSON."""
    payload = {
        "id": str(entity_id),
        "created_at": created_at.isoformat(),
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode a base64 cursor into a dict with 'id' (UUID) and 'created_at' (datetime).

    Raises ValueError if the cursor is malformed.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw)
        return {
            "id": UUID(data["id"]),
            "created_at": datetime.fromisoformat(data["created_at"]),
        }
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid cursor: {cursor}") from exc


# ---------------------------------------------------------------------------
# Pagination value objects
# ---------------------------------------------------------------------------

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MIN_LIMIT = 1


@dataclass(frozen=True)
class Pagination:
    """Cursor-based pagination parameters."""

    cursor: str | None = None
    limit: int = DEFAULT_LIMIT

    def __post_init__(self) -> None:
        if self.limit < MIN_LIMIT:
            object.__setattr__(self, "limit", MIN_LIMIT)
        elif self.limit > MAX_LIMIT:
            object.__setattr__(self, "limit", MAX_LIMIT)


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """Result wrapper for paginated queries."""

    data: list[T] = field(default_factory=list)
    total: int | None = None
    has_next: bool = False
    next_cursor: str | None = None
