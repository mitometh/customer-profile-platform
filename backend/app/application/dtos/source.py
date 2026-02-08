"""DTOs for the source management context."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SourceSummaryDTO:
    """Compact source representation for list views."""

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class SourceDetailDTO:
    """Full source detail (excludes api_token_hash)."""

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SourceCreateResultDTO:
    """Returned after source creation — includes the raw API token (shown once)."""

    id: UUID
    name: str
    api_token: str
    is_active: bool
    created_at: datetime
