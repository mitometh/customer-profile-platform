from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Single error entry returned in error responses."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    """Top-level error response wrapper."""

    model_config = ConfigDict(frozen=True)

    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata included alongside list responses."""

    model_config = ConfigDict(frozen=True)

    total: int | None = None
    limit: int
    has_next: bool
    next_cursor: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response containing data and pagination metadata."""

    data: list[T]
    pagination: PaginationMeta
