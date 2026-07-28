"""initial schema: alerts, work_orders, work_order_part_lines

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-27 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

# JSON type: JSONB on PostgreSQL, generic JSON elsewhere.
JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    """Create the initial tables."""
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("equipment_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="NEW",
        ),
        sa.Column("issuer_name", sa.String(length=255), nullable=True),
        sa.Column("machine_details", JSONType, nullable=True),
        sa.Column("readings_snapshot", JSONType, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("alert_id", sa.String(length=36), nullable=False),
        sa.Column("equipment_id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("issuer_name", sa.String(length=255), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("machine_details", JSONType, nullable=True),
        sa.Column("readings_snapshot", JSONType, nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        # Enforce one work order per alert.
        sa.UniqueConstraint("alert_id", name="uq_work_orders_alert_id"),
    )
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_priority", "work_orders", ["priority"])
    op.create_index("ix_work_orders_created_at", "work_orders", ["created_at"])

    op.create_table(
        "work_order_part_lines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("work_order_id", sa.String(length=36), nullable=False),
        sa.Column("part_name", sa.String(length=255), nullable=False),
        sa.Column(
            "used", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
    )
    op.create_index(
        "ix_wo_part_lines_work_order_id",
        "work_order_part_lines",
        ["work_order_id"],
    )


def downgrade() -> None:
    """Drop the initial tables."""
    op.drop_index(
        "ix_wo_part_lines_work_order_id", table_name="work_order_part_lines"
    )
    op.drop_table("work_order_part_lines")
    op.drop_index("ix_work_orders_created_at", table_name="work_orders")
    op.drop_index("ix_work_orders_priority", table_name="work_orders")
    op.drop_index("ix_work_orders_status", table_name="work_orders")
    op.drop_table("work_orders")
    op.drop_table("alerts")
