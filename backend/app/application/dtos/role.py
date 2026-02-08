"""DTOs for the role & permission management context."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True)
class PermissionDTO:
    """Lightweight permission representation."""

    id: UUID
    code: str
    description: str | None


@dataclass(frozen=True)
class RoleSummaryDTO:
    """Role summary for list responses (includes permission count)."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_system: bool
    permission_count: int
    created_at: datetime


@dataclass(frozen=True)
class RoleDetailDTO:
    """Full role detail with resolved permissions and user count."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionDTO] = field(default_factory=list)
    user_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=UTC))
