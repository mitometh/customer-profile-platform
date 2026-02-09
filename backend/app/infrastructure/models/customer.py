"""Customer model for customer management context."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class CustomerModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    signup_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_customers_company_name",
            "company_name",
            postgresql_using="gin",
            postgresql_ops={"company_name": "gin_trgm_ops"},
        ),
        Index("ix_customers_deleted_at", "deleted_at"),
    )

    # --- Relationships ---
    source: Mapped["SourceModel"] = relationship(
        "SourceModel",
        lazy="selectin",
    )
    events: Mapped[list["EventModel"]] = relationship(
        "EventModel",
        back_populates="customer",
        lazy="select",
    )
