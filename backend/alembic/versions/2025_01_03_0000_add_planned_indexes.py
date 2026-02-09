"""add_planned_indexes

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-03 00:00:00.000000+00:00

Adds planned indexes from ARCHITECTURE.md:
- GIN trigram index on customers.company_name for fuzzy name search
- Index on customer_metrics.customer_id for fast metrics lookup
- Index on users.role_id for RBAC permission resolution
- Soft-delete indexes on deleted_at for all mutable tables
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Drop the existing btree index on company_name and replace with GIN trigram
    op.drop_index("ix_customers_company_name", table_name="customers")
    op.execute(
        "CREATE INDEX ix_customers_company_name ON customers "
        "USING gin (company_name gin_trgm_ops)"
    )

    # Fast metrics lookup by customer
    op.create_index("ix_customer_metrics_customer_id", "customer_metrics", ["customer_id"])

    # RBAC permission resolution
    op.create_index("ix_users_role_id", "users", ["role_id"])

    # Soft-delete filtering indexes (all mutable tables)
    op.create_index("ix_roles_deleted_at", "roles", ["deleted_at"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])
    op.create_index("ix_sources_deleted_at", "sources", ["deleted_at"])
    op.create_index("ix_customers_deleted_at", "customers", ["deleted_at"])
    op.create_index("ix_events_deleted_at", "events", ["deleted_at"])
    op.create_index("ix_customer_metrics_deleted_at", "customer_metrics", ["deleted_at"])
    op.create_index("ix_metric_definitions_deleted_at", "metric_definitions", ["deleted_at"])
    op.create_index("ix_chat_sessions_deleted_at", "chat_sessions", ["deleted_at"])


def downgrade() -> None:
    # Drop soft-delete indexes
    op.drop_index("ix_chat_sessions_deleted_at", table_name="chat_sessions")
    op.drop_index("ix_metric_definitions_deleted_at", table_name="metric_definitions")
    op.drop_index("ix_customer_metrics_deleted_at", table_name="customer_metrics")
    op.drop_index("ix_events_deleted_at", table_name="events")
    op.drop_index("ix_customers_deleted_at", table_name="customers")
    op.drop_index("ix_sources_deleted_at", table_name="sources")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_index("ix_roles_deleted_at", table_name="roles")

    # Drop RBAC and metrics indexes
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_customer_metrics_customer_id", table_name="customer_metrics")

    # Revert trigram index to plain btree
    op.drop_index("ix_customers_company_name", table_name="customers")
    op.create_index("ix_customers_company_name", "customers", ["company_name"])

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
