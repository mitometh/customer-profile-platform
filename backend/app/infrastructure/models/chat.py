"""Chat models for the conversational agent context.

Two models:
- ChatSessionModel: user chat sessions with metadata
- ChatMessageModel: append-only chat messages (no audit, no soft delete)
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, SoftDeleteMixin, TimestampMixin


class ChatSessionModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    messages: Mapped[list["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        lazy="select",
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="selectin",
    )


class ChatMessageModel(Base):
    """Append-only chat message. No mixins (no audit, no soft delete)."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    tool_calls: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- Relationships ---
    session: Mapped["ChatSessionModel"] = relationship(
        "ChatSessionModel",
        back_populates="messages",
        lazy="selectin",
    )
