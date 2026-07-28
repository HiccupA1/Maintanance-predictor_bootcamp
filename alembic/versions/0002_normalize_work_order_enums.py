"""Normalize work-order enums and enforce their allowed values."""

import sqlalchemy as sa

from alembic import op

revision = "0002_normalize_work_order_enums"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Normalize legacy casing and reject values outside the contract."""
    op.execute(
        sa.text(
            "UPDATE work_orders "
            "SET priority = UPPER(TRIM(priority)), "
            "status = UPPER(TRIM(status))"
        )
    )

    invalid = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT id, priority, status FROM work_orders "
                "WHERE priority NOT IN ('CRITICAL', 'HIGH', 'MEDIUM') "
                "OR status NOT IN ('OPEN', 'CLOSED') LIMIT 1"
            )
        )
        .first()
    )
    if invalid is not None:
        raise RuntimeError(
            "Cannot apply work-order enum constraints: "
            f"row {invalid.id!r} has priority={invalid.priority!r}, "
            f"status={invalid.status!r}."
        )

    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.create_check_constraint(
            "ck_work_orders_priority",
            "priority IN ('CRITICAL', 'HIGH', 'MEDIUM')",
        )
        batch_op.create_check_constraint(
            "ck_work_orders_status",
            "status IN ('OPEN', 'CLOSED')",
        )


def downgrade() -> None:
    """Remove enum constraints while preserving normalized data."""
    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.drop_constraint("ck_work_orders_status", type_="check")
        batch_op.drop_constraint("ck_work_orders_priority", type_="check")
