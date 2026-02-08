"""Role, Permission, and RolePermission models for identity & access context."""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, SoftDeleteMixin, TimestampMixin


class RoleModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # --- Relationships ---
    permissions: Mapped[list["PermissionModel"]] = relationship(
        "PermissionModel",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    users: Mapped[list["UserModel"]] = relationship(
        "UserModel",
        back_populates="role",
        lazy="select",
    )


class PermissionModel(Base):
    """Seed-only, immutable permission record. No mixins."""

    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Relationships ---
    roles: Mapped[list["RoleModel"]] = relationship(
        "RoleModel",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="select",
    )


class RolePermissionModel(Base):
    """Junction table linking roles to permissions. Composite PK, no mixins."""

    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("roles.id"),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("permissions.id"),
        primary_key=True,
    )
