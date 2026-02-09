"""User model for identity & access context."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class UserModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_users_deleted_at", "deleted_at"),
    )

    # --- Relationships ---
    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        back_populates="users",
        lazy="selectin",
    )
