"""Add MVP equipment, parameter, reading, and alert domain tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_mvp_domains"
down_revision = "0002_normalize_work_order_enums"
branch_labels = None
depends_on = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    """Create MVP domain tables and add work-order closure identity."""
    op.create_table(
        "equipment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("equipment_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("criticality", sa.Integer(), nullable=False),
        sa.Column("last_service_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_equipment_equipment_id", "equipment", ["equipment_id"])

    op.create_table(
        "parameters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("equipment_id", sa.String(36), sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(100), nullable=False),
        sa.Column("min_threshold", sa.Float()),
        sa.Column("max_threshold", sa.Float()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("suggested_action", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_parameters_equipment_id", "parameters", ["equipment_id"])

    op.create_table(
        "readings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("equipment_id", sa.String(36), sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("parameter_id", sa.String(36), sa.ForeignKey("parameters.id"), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entered_by", sa.String(255), nullable=False, server_default="dev"),
        sa.Column("modified_by", sa.String(255)),
        sa.Column("modified_at", sa.DateTime(timezone=True)),
        sa.Column("modification_reason", sa.Text()),
    )
    op.create_index("ix_readings_equipment_id", "readings", ["equipment_id"])
    op.create_index("ix_readings_parameter_id", "readings", ["parameter_id"])
    op.create_index("ix_readings_timestamp", "readings", ["timestamp"])

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("parameter_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("priority", sa.String(16), nullable=False, server_default="MEDIUM"))
        batch_op.add_column(sa.Column("current_value", sa.String(255)))
        batch_op.add_column(sa.Column("breach_timestamp", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("min_threshold", sa.Float()))
        batch_op.add_column(sa.Column("max_threshold", sa.Float()))
        batch_op.add_column(sa.Column("suggested_action", sa.Text()))
        batch_op.add_column(sa.Column("why_priority", sa.Text()))
        batch_op.create_foreign_key(
            "fk_alerts_parameter_id", "parameters", ["parameter_id"], ["id"]
        )
        batch_op.create_index("ix_alerts_parameter_id", ["parameter_id"])

    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.add_column(sa.Column("closed_by", sa.String(255)))


def downgrade() -> None:
    """Remove MVP domain tables and closure identity."""
    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.drop_column("closed_by")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_index("ix_alerts_parameter_id")
        batch_op.drop_constraint("fk_alerts_parameter_id", type_="foreignkey")
        for name in (
            "why_priority",
            "suggested_action",
            "max_threshold",
            "min_threshold",
            "breach_timestamp",
            "current_value",
            "priority",
            "parameter_id",
        ):
            batch_op.drop_column(name)
    op.drop_index("ix_readings_timestamp", table_name="readings")
    op.drop_index("ix_readings_parameter_id", table_name="readings")
    op.drop_index("ix_readings_equipment_id", table_name="readings")
    op.drop_table("readings")
    op.drop_index("ix_parameters_equipment_id", table_name="parameters")
    op.drop_table("parameters")
    op.drop_index("ix_equipment_equipment_id", table_name="equipment")
    op.drop_table("equipment")
