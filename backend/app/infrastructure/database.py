from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


class _DatabaseHolder:
    """Module-level state holder. Avoids ``global`` keyword."""

    engine = None
    session_factory = None


_holder = _DatabaseHolder()


def _get_engine():
    if _holder.engine is None:
        settings = get_settings()
        _holder.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
    return _holder.engine


def _get_session_factory():
    if _holder.session_factory is None:
        _holder.session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _holder.session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a database session for dependency injection."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a read-only database session (no auto-commit)."""
    factory = _get_session_factory()
    async with factory() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose the engine and release all connections. Called at shutdown."""
    if _holder.engine is not None:
        await _holder.engine.dispose()
        _holder.engine = None
        _holder.session_factory = None
