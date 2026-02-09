"""Repository protocol definitions for Dependency Inversion.

Each Protocol captures only the methods that the application/service layer
actually calls, keeping the core layer decoupled from SQLAlchemy internals.
Return types use ``Any`` instead of concrete ORM models to avoid circular
imports between core and infrastructure layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from app.core.types import PaginatedResult, Pagination


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


@runtime_checkable
class CustomerRepository(Protocol):
    async def search(self, query: str, pagination: Pagination) -> PaginatedResult[Any]: ...
    async def get_detail(self, customer_id: UUID) -> Any | None: ...
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...
    async def list(self, pagination: Pagination) -> PaginatedResult[Any]: ...
    async def create(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def soft_delete(self, entity_id: UUID, deleted_by: UUID | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


@runtime_checkable
class EventRepository(Protocol):
    async def list_for_customer(
        self,
        customer_id: UUID,
        event_type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        order: str = "desc",
        pagination: Pagination = ...,
    ) -> PaginatedResult[Any]: ...

    async def get_recent_for_customer(self, customer_id: UUID, limit: int = 10) -> list[Any]: ...


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> Any | None: ...
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...
    async def update(self, entity: Any) -> Any: ...
    async def create(self, entity: Any) -> Any: ...
    async def email_exists(self, email: str) -> bool: ...
    async def list_users(self, pagination: Pagination) -> PaginatedResult[Any]: ...


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


@runtime_checkable
class RoleRepository(Protocol):
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...
    async def get_by_name(self, name: str) -> Any | None: ...
    async def get_permissions_for_role(self, role_id: UUID) -> list[str]: ...
    async def list_roles(self, pagination: Pagination) -> PaginatedResult[Any]: ...
    async def name_exists(self, name: str, exclude_id: UUID | None = None) -> bool: ...
    async def get_user_count(self, role_id: UUID) -> int: ...
    async def get_all_permissions(self) -> list[Any]: ...
    async def get_permissions_by_ids(self, permission_ids: list[UUID]) -> list[Any]: ...
    async def get_permission_models_for_role(self, role_id: UUID) -> list[Any]: ...
    async def replace_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None: ...
    async def create(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def soft_delete(self, entity_id: UUID, deleted_by: UUID | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Metric Definition
# ---------------------------------------------------------------------------


@runtime_checkable
class MetricDefinitionRepository(Protocol):
    async def list_all(self) -> list[Any]: ...
    async def get_by_name(self, name: str) -> Any | None: ...
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...
    async def create(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def soft_delete(self, entity_id: UUID, deleted_by: UUID | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Customer Metric
# ---------------------------------------------------------------------------


@runtime_checkable
class CustomerMetricRepository(Protocol):
    async def get_for_customer(self, customer_id: UUID) -> list[Any]: ...


# ---------------------------------------------------------------------------
# Customer Metric History
# ---------------------------------------------------------------------------


@runtime_checkable
class CustomerMetricHistoryRepository(Protocol):
    async def get_trend(
        self,
        customer_id: UUID,
        metric_definition_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 90,
    ) -> list[Any]: ...


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------


@runtime_checkable
class SourceRepository(Protocol):
    async def list(self, pagination: Pagination) -> PaginatedResult[Any]: ...
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...
    async def get_by_name(self, name: str) -> Any | None: ...
    async def create(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def soft_delete(self, entity_id: UUID, deleted_by: UUID | None = None) -> None: ...
    async def get_by_token_hash(self, token_hash: str) -> Any | None: ...


# ---------------------------------------------------------------------------
# Chat Session
# ---------------------------------------------------------------------------


@runtime_checkable
class ChatSessionRepository(Protocol):
    async def get_with_messages(self, session_id: UUID) -> Any | None: ...
    async def create(self, entity: Any) -> Any: ...
    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        sources: dict | None = None,
        tool_calls: dict | None = None,
    ) -> Any: ...
    async def update_session_metadata(self, session_id: UUID) -> None: ...
    async def get_by_id(self, entity_id: UUID) -> Any | None: ...


# ---------------------------------------------------------------------------
# Token Cache
# ---------------------------------------------------------------------------


@runtime_checkable
class TokenCache(Protocol):
    async def validate_token(self, token_hash: str) -> dict | None: ...
    async def cache_token(self, token_hash: str, source_info: dict, ttl: int = 300) -> None: ...
    async def invalidate_token(self, token_hash: str) -> None: ...


# ---------------------------------------------------------------------------
# Message Broker (Publisher)
# ---------------------------------------------------------------------------


@runtime_checkable
class MessagePublisher(Protocol):
    async def publish(self, message: dict) -> None: ...
