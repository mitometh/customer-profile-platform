from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class EventBus(Protocol):
    """Protocol for publishing and subscribing to domain events."""

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers."""
        ...

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Coroutine[Any, Any, None]],
    ) -> None:
        """Register a handler for a specific event type."""
        ...
