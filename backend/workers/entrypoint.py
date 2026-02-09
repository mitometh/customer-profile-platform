"""Shared worker entry point.

Usage: python -m workers.entrypoint <worker_type>
  worker_type: data_store | metrics | alerts
"""

import asyncio
import signal
import sys

from app.config import get_settings
from app.infrastructure.broker import BaseConsumer
from app.infrastructure.database import get_session
from app.infrastructure.logging import configure_logging, get_logger

WORKER_MAP: dict[str, tuple[str, str, str]] = {
    "data_store": ("q.data-store", "workers.data_store", "process_message"),
    "metrics": ("q.metrics", "workers.metrics", "process_message"),
    "alerts": ("q.alerts", "workers.alerts", "process_message"),
}


async def run_worker(worker_type: str) -> None:
    """Bootstrap and run a single worker process until shutdown signal."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
    logger = get_logger("worker")

    if worker_type not in WORKER_MAP:
        logger.error("Unknown worker type", worker_type=worker_type)
        sys.exit(1)

    queue_name, module_path, handler_name = WORKER_MAP[worker_type]

    # Import handler dynamically
    module = __import__(module_path, fromlist=[handler_name])
    handler = getattr(module, handler_name)

    # Set up graceful shutdown
    shutdown_event = asyncio.Event()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Received shutdown signal", signal=sig)
        shutdown_event.set()

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Create consumer and start consuming
    consumer = BaseConsumer()
    await consumer.connect()

    logger.info("Worker started", worker_type=worker_type, queue=queue_name)

    async def on_message(message: dict) -> None:
        async for session in get_session():
            try:
                await handler(message, session)
            except Exception as exc:
                await session.rollback()
                logger.error(
                    "Message processing failed",
                    error=str(exc),
                    worker_type=worker_type,
                )

    await consumer.consume(queue_name, on_message)

    # Wait for shutdown
    await shutdown_event.wait()
    await consumer.close()
    logger.info("Worker stopped", worker_type=worker_type)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m workers.entrypoint <worker_type>")
        sys.exit(1)
    asyncio.run(run_worker(sys.argv[1]))
