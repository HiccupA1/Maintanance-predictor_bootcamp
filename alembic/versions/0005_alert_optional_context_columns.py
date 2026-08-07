"""Add optional context columns to alerts.

This fixes an ORM-vs-DB schema mismatch where the SQLAlchemy Alert model maps
issuer_name, machine_details, and readings_snapshot but the database schema
may not have those columns yet (e.g., Supabase-managed schema drift).

Revision ID: 0005_alert_optional_context_columns
Revises: 0004_user_profiles_roles
Create Date: 2026-08-07 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_alert_optional_context_columns"
down_revision = "0004_user_profiles_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing optional context fields on alerts."""
    # JSON type: JSONB on PostgreSQL, generic JSON elsewhere.
    json_type = sa.JSON().with_variant(JSONB, "postgresql")

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("issuer_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("machine_details", json_type, nullable=True))
        batch_op.add_column(sa.Column("readings_snapshot", json_type, nullable=True))


def downgrade() -> None:
    """Remove optional context fields from alerts."""
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_column("readings_snapshot")
        batch_op.drop_column("machine_details")
        batch_op.drop_column("issuer_name")
