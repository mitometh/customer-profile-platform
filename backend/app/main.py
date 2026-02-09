from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.infrastructure.logging import RequestLoggingMiddleware, configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of external connections.

    Startup:
        - Configure structured logging
        - Eagerly create the database engine (validates the connection string)
        - Create the Redis client
        - Connect the RabbitMQ publisher (best-effort; workers may not need it)

    Shutdown:
        - Dispose the database engine and release pool connections
        - Close the Redis client
        - Close the RabbitMQ publisher
    """
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

    # Import lazily so that module-level side effects stay controlled
    from app.infrastructure.broker import close_publisher, get_publisher
    from app.infrastructure.cache import close_redis, get_redis
    from app.infrastructure.database import dispose_engine

    # Warm up connections and store on app.state for lifecycle management
    redis = get_redis()
    app.state.redis = redis

    # Connect RabbitMQ publisher (best-effort; ingestion still works without it)
    from app.infrastructure.logging import get_logger

    _startup_logger = get_logger("startup")
    publisher = get_publisher()
    app.state.publisher = publisher
    try:
        await publisher.connect()
    except Exception as exc:
        _startup_logger.warning("RabbitMQ publisher connection failed during startup", error=str(exc))

    yield

    # Teardown
    await close_publisher()
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Customer 360 Insights Agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ----- Middleware (order matters: outermost first) -----
    from app.api.middleware import (
        AuthMiddleware,
        add_cors_middleware,
        app_error_handler,
        unhandled_error_handler,
    )
    from app.core.exceptions import AppError

    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    add_cors_middleware(app)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ----- Routers -----
    from app.api import router as api_router
    from app.api.routes.ingestion import router as ingestion_router

    app.include_router(api_router, prefix="/api")
    app.include_router(ingestion_router, prefix="/hooks", tags=["ingestion"])

    return app
