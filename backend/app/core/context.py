"""Caller context for request authorization."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions import ForbiddenError


@dataclass(frozen=True)
class CallerContext:
    """Immutable authorization context for the current caller.

    Replaces passing raw permissions: list[str] through every service method.
    """

    user_id: UUID
    email: str
    full_name: str
    role: str
    permissions: frozenset[str]

    def has_permission(self, permission: str) -> bool:
        """Check whether the caller has a specific permission."""
        return permission in self.permissions

    def require_permission(self, permission: str) -> None:
        """Raise ForbiddenError if the caller lacks the given permission."""
        if permission not in self.permissions:
            raise ForbiddenError(permission)
