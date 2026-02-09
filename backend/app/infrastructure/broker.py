import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage

from app.config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "events.fanout"

QUEUE_DATA_STORE = "q.data-store"
QUEUE_METRICS = "q.metrics"
QUEUE_ALERTS = "q.alerts"


class _BrokerHolder:
    """Module-level state holder. Avoids ``global`` keyword."""

    publisher: "RabbitMQPublisher | None" = None


_holder = _BrokerHolder()


def get_publisher() -> "RabbitMQPublisher":
    """Return a singleton RabbitMQPublisher instance."""
    if _holder.publisher is None:
        _holder.publisher = RabbitMQPublisher()
    return _holder.publisher


async def close_publisher() -> None:
    """Close the global publisher. Called at shutdown."""
    if _holder.publisher is not None:
        await _holder.publisher.close()
        _holder.publisher = None


class RabbitMQPublisher:
    """Publishes JSON messages to a RabbitMQ fanout exchange."""

    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        """Establish connection, channel, and declare the fanout exchange."""
        settings = get_settings()
        self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.FANOUT,
            durable=True,
        )

    async def publish(self, message: dict[str, Any]) -> None:
        """Publish a JSON-serialised message to the fanout exchange.

        Args:
            message: Dict payload to serialise as JSON.
        """
        if self._exchange is None:
            raise RuntimeError("Publisher is not connected. Call connect() first.")

        body = json.dumps(message, default=str).encode("utf-8")
        await self._exchange.publish(
            Message(
                body=body,
                content_type="application/json",
            ),
            routing_key="",
        )

    async def close(self) -> None:
        """Close channel and connection."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
        self._exchange = None


class BaseConsumer:
    """Consumes messages from a RabbitMQ queue bound to the fanout exchange."""

    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        """Establish connection and channel."""
        settings = get_settings()
        self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """Declare a queue, bind it to the fanout exchange, and start consuming.

        The callback receives the deserialized JSON payload as a dict.
        """
        if self._channel is None:
            raise RuntimeError("Consumer is not connected. Call connect() first.")

        exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.FANOUT,
            durable=True,
        )
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange)

        async def _on_message(msg: AbstractIncomingMessage) -> None:
            try:
                body = json.loads(msg.body.decode("utf-8"))
                await callback(body)
                await msg.ack()
            except json.JSONDecodeError:
                logger.error("Malformed message body, discarding", extra={"queue": queue_name})
                await msg.ack()
            except Exception:
                if msg.redelivered:
                    logger.error(
                        "Message failed after redelivery, discarding",
                        extra={"queue": queue_name},
                    )
                    await msg.ack()
                else:
                    logger.warning("Message processing failed, requeuing", extra={"queue": queue_name})
                    await msg.nack(requeue=True)

        await queue.consume(_on_message)

    async def close(self) -> None:
        """Close channel and connection."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
