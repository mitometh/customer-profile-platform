"""add_role_is_system_and_rbac_permissions

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-02 00:00:00.000000+00:00

Adds is_system boolean column to roles table and seeds roles.read / roles.manage
permissions into the permissions and role_permissions tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_system column to roles table (default false)
    op.add_column(
        "roles",
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # 2. Mark the 5 seeded roles as system roles
    op.execute("UPDATE roles SET is_system = true WHERE name IN ('sales', 'support', 'cs_manager', 'ops', 'admin')")

    # 3. Insert new permissions: roles.read and roles.manage
    op.execute(
        "INSERT INTO permissions (id, code, description) VALUES "
        "(gen_random_uuid(), 'roles.read', 'View roles and their permission assignments'), "
        "(gen_random_uuid(), 'roles.manage', 'Create, update, delete roles and assign/remove permissions')"
    )

    # 4. Grant roles.read and roles.manage to admin role
    op.execute(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r, permissions p "
        "WHERE r.name = 'admin' AND p.code IN ('roles.read', 'roles.manage')"
    )


def downgrade() -> None:
    # Remove role_permissions for the new permissions
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE code IN ('roles.read', 'roles.manage'))"
    )

    # Remove the new permissions
    op.execute("DELETE FROM permissions WHERE code IN ('roles.read', 'roles.manage')")

    # Remove is_system column
    op.drop_column("roles", "is_system")
