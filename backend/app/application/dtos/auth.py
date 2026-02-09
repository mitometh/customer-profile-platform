"""DTOs for the identity & access context."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CurrentUserDTO:
    """Lightweight representation of the authenticated user, available via DI."""

    id: UUID
    email: str
    full_name: str
    role: str
    permissions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LoginResultDTO:
    """Returned by AuthService.login with the JWT and user info."""

    access_token: str
    token_type: str
    user: CurrentUserDTO


@dataclass(frozen=True)
class UserSummaryDTO:
    """Lightweight user representation for list and detail responses."""

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
