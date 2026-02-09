"""Event model for activity tracking context.

Events are append-only business facts. No updated_at/updated_by.
Soft deletion is supported for compliance and data-correction workflows.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, SoftDeleteMixin


class EventModel(Base, SoftDeleteMixin):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID | None] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(pg.UUID(as_uuid=True), nullable=True)

    # --- Indexes ---
    __table_args__ = (
        Index("ix_events_customer_occurred", "customer_id", occurred_at.desc()),
        Index(
            "ix_events_customer_type_occurred",
            "customer_id",
            "event_type",
            occurred_at.desc(),
        ),
        Index("ix_events_deleted_at", "deleted_at"),
    )

    # --- Relationships ---
    customer: Mapped["CustomerModel"] = relationship(
        "CustomerModel",
        back_populates="events",
        lazy="selectin",
    )
    source: Mapped["SourceModel"] = relationship(
        "SourceModel",
        lazy="selectin",
    )
