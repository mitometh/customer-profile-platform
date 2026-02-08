from collections.abc import Callable, Coroutine
from typing import Any

from app.core.events import DomainEvent, EventBus


class InMemoryEventBus:
    """In-process event bus implementing the EventBus protocol.

    Handlers are stored in memory and called sequentially when an event
    is published. Suitable for within-process domain events; not for
    cross-process fan-out (use RabbitMQ for that).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[DomainEvent], Coroutine[Any, Any, None]]]] = {}

    async def publish(self, event: DomainEvent) -> None:
        """Invoke every handler registered for the event's type."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            await handler(event)

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Coroutine[Any, Any, None]],
    ) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)


# Module-level check that InMemoryEventBus satisfies the EventBus protocol.
_bus_check: EventBus = InMemoryEventBus()  # type: ignore[assignment]
