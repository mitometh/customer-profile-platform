"""Metric models for the metrics engine context.

Three models:
- MetricDefinitionModel: self-describing metric catalog entries
- CustomerMetricModel: current metric values per customer
- CustomerMetricHistoryModel: append-only historical snapshots for trend analysis
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class MetricDefinitionModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "metric_definitions"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)


class CustomerMetricModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "customer_metrics"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    metric_definition_id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False
    )
    metric_value: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "metric_definition_id",
            name="uq_customer_metric_definition",
        ),
    )

    # --- Relationships ---
    customer: Mapped["CustomerModel"] = relationship(
        "CustomerModel",
        lazy="selectin",
    )
    metric_definition: Mapped["MetricDefinitionModel"] = relationship(
        "MetricDefinitionModel",
        lazy="selectin",
    )


class CustomerMetricHistoryModel(Base):
    """Append-only historical snapshot. No mixins (no audit, no soft delete)."""

    __tablename__ = "customer_metric_history"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    metric_definition_id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False
    )
    metric_value: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index(
            "ix_customer_metric_history_lookup",
            "customer_id",
            "metric_definition_id",
            "recorded_at",
        ),
    )
