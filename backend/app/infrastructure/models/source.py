"""Source model for source integration context."""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class SourceModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_sources_deleted_at", "deleted_at"),
    )
