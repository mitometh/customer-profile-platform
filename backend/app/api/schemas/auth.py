"""Pydantic schemas for auth and user management endpoints."""

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """POST /api/auth/login request body."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class CurrentUserSchema(BaseModel):
    """Authenticated user with resolved permissions (login response / GET /me)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    permissions: list[str]


class LoginResponse(BaseModel):
    """POST /api/auth/login response body."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str
    user: CurrentUserSchema


class UserCreateRequest(BaseModel):
    """POST /api/users request body."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    full_name: str = Field(..., max_length=255)
    role: Literal["sales", "support", "cs_manager", "ops", "admin"]
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity: at least one uppercase, one lowercase, one digit."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdateRequest(BaseModel):
    """PATCH /api/users/{user_id} request body."""

    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = Field(None, max_length=255)
    role_id: UUID | None = None
    is_active: bool | None = None


class UserSummarySchema(BaseModel):
    """User summary for list and detail responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
