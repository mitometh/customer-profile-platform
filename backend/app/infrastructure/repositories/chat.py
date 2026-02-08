"""Chat session repository for the conversational agent context."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.chat import ChatMessageModel, ChatSessionModel
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyChatSessionRepository(BaseRepository[ChatSessionModel]):
    """Data-access layer for chat session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChatSessionModel)

    async def get_user_sessions(self, user_id: UUID, limit: int = 10) -> list[ChatSessionModel]:
        """Get recent chat sessions for a user, ordered by last_message_at DESC.

        Only returns active, non-soft-deleted sessions.
        """
        stmt = (
            select(ChatSessionModel)
            .where(
                ChatSessionModel.user_id == user_id,
                ChatSessionModel.is_active.is_(True),
            )
            .order_by(ChatSessionModel.last_message_at.desc())
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(self, session_id: UUID) -> ChatSessionModel | None:
        """Get a session with all messages eagerly loaded.

        Returns None if the session does not exist or is soft-deleted.
        Messages are ordered by created_at ASC for chronological display.
        """
        stmt = (
            select(ChatSessionModel)
            .options(
                selectinload(ChatSessionModel.messages),
            )
            .where(ChatSessionModel.id == session_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        sources: dict | None = None,
        tool_calls: dict | None = None,
    ) -> ChatMessageModel:
        """Append a message to a chat session.

        Creates the ChatMessageModel, flushes, and returns it.
        Does NOT update session metadata (call ``update_session_metadata``
        separately after both user and assistant messages are persisted).
        """
        message = ChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            tool_calls=tool_calls,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def update_session_metadata(self, session_id: UUID) -> None:
        """Update last_message_at and message_count for a session.

        Recomputes message_count from the actual number of messages
        and sets last_message_at to the current UTC time.
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj is None:
            return

        # Count messages for this session
        count_stmt = select(func.count(ChatMessageModel.id)).where(ChatMessageModel.session_id == session_id)
        count_result = await self._session.execute(count_stmt)
        message_count = count_result.scalar_one()

        session_obj.message_count = message_count
        session_obj.last_message_at = datetime.now(UTC)
        await self._session.flush()
