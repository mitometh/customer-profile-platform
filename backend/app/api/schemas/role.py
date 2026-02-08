"""Pydantic schemas for role & permission management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionSchema(BaseModel):
    """Permission item for list and role detail responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str | None = None


class RoleSummarySchema(BaseModel):
    """Role summary for list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    permission_count: int
    created_at: datetime


class RoleDetailSchema(BaseModel):
    """Full role detail with permissions and user count."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    permissions: list[PermissionSchema]
    user_count: int
    created_at: datetime
    updated_at: datetime


class RoleCreateRequest(BaseModel):
    """POST /api/roles request body."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine-readable identifier. Lowercase alphanumeric + underscores.",
    )
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    permissions: list[UUID] = Field(
        ...,
        min_length=1,
        description="Array of permission IDs to assign. At least one required.",
    )


class RoleUpdateRequest(BaseModel):
    """PATCH /api/roles/{id} request body."""

    display_name: str | None = Field(None, max_length=100)
    description: str | None = None
    permissions: list[UUID] | None = Field(
        None,
        min_length=1,
        description="Full replacement of role's permission set. At least one when provided.",
    )
