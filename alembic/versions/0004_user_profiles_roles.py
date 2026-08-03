"""Add user_profiles for Supabase user role persistence."""

import sqlalchemy as sa
from alembic import op

revision = "0004_user_profiles_roles"
down_revision = "0003_mvp_domains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_profiles table for persisted application roles."""
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("supabase_user_id", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column(
            "role",
            sa.String(32),
            nullable=False,
            server_default="Operator",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_user_profiles_supabase_user_id",
        "user_profiles",
        ["supabase_user_id"],
    )
    op.create_index("ix_user_profiles_email", "user_profiles", ["email"])


def downgrade() -> None:
    """Drop user_profiles table."""
    op.drop_index("ix_user_profiles_email", table_name="user_profiles")
    op.drop_index(
        "ix_user_profiles_supabase_user_id", table_name="user_profiles"
    )
    op.drop_table("user_profiles")
