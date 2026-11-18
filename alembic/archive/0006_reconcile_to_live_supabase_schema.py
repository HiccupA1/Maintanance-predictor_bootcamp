"""Reconcile Alembic schema to match live Supabase public schema.

Revision ID: 0006_reconcile_to_live_supabase_schema
Revises: 0005_alert_optional_context_columns
Create Date: 2026-08-07

This migration aligns the repository-managed Alembic schema with the *live*
Supabase schema used in production. The live DB is treated as source of truth.

Key changes:
- Convert string UUID columns to PostgreSQL UUID with gen_random_uuid() defaults.
- Align FK nullability + ON DELETE behaviors.
- Replace work_orders structure with live fields (title/assigned_to, no alert_id).
- Drop work_order_part_lines table (not present in live DB).
- Align alerts fields/defaults and drop non-existent updated_at mapping if present.

IMPORTANT: This migration may be a no-op on environments already matching live.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_reconcile_to_live_supabase_schema"
down_revision = "0005_alert_optional_context_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply reconciliation changes."""
    uuid = postgresql.UUID(as_uuid=False)

    # equipment
    with op.batch_alter_table("equipment") as b:
        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        b.alter_column("equipment_id", type_=sa.Text())
        b.alter_column("name", type_=sa.Text())
        b.alter_column("location", type_=sa.Text(), server_default="''::text")
        b.alter_column("type", type_=sa.Text(), server_default="''::text")
        b.alter_column("created_at", server_default=sa.text("now()"))
        b.alter_column("updated_at", server_default=sa.text("now()"))

    # parameters
    with op.batch_alter_table("parameters") as b:
        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        b.alter_column("equipment_id", type_=uuid, postgresql_using="equipment_id::uuid")
        b.alter_column("name", type_=sa.Text())
        b.alter_column("unit", type_=sa.Text(), server_default="''::text")
        b.alter_column("min_threshold", type_=sa.Float(precision=53))
        b.alter_column("max_threshold", type_=sa.Float(precision=53))
        b.alter_column("active", server_default=sa.text("true"))
        b.alter_column("suggested_action", type_=sa.Text())
        b.alter_column("created_at", server_default=sa.text("now()"))
        b.alter_column("updated_at", server_default=sa.text("now()"))
        # Ensure FK ondelete cascade matches live (recreate constraint if needed).
        b.drop_constraint("parameters_equipment_id_fkey", type_="foreignkey")
        b.create_foreign_key(
            "parameters_equipment_id_fkey",
            "equipment",
            ["equipment_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # readings
    with op.batch_alter_table("readings") as b:
        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        b.alter_column("equipment_id", type_=uuid, postgresql_using="equipment_id::uuid")
        b.alter_column("parameter_id", type_=uuid, postgresql_using="parameter_id::uuid")
        b.alter_column("value", type_=sa.Text())
        b.alter_column("timestamp", server_default=sa.text("now()"))
        b.alter_column("entered_by", type_=sa.Text(), server_default="'dev'::text")
        b.alter_column("modified_by", type_=sa.Text())
        b.alter_column("modification_reason", type_=sa.Text())
        b.alter_column("created_at", existing_type=None, existing_nullable=True)  # no-op safeguard
        b.drop_constraint("readings_equipment_id_fkey", type_="foreignkey")
        b.create_foreign_key(
            "readings_equipment_id_fkey",
            "equipment",
            ["equipment_id"],
            ["id"],
            ondelete="CASCADE",
        )
        b.drop_constraint("readings_parameter_id_fkey", type_="foreignkey")
        b.create_foreign_key(
            "readings_parameter_id_fkey",
            "parameters",
            ["parameter_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # alerts
    with op.batch_alter_table("alerts") as b:
        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        b.alter_column("equipment_id", type_=uuid, postgresql_using="equipment_id::uuid", nullable=True)
        b.alter_column("parameter_id", type_=uuid, postgresql_using="parameter_id::uuid", nullable=True)
        b.alter_column("priority", type_=sa.Text(), server_default="'MEDIUM'::text")
        b.alter_column("current_value", type_=sa.Text())
        b.alter_column("min_threshold", type_=sa.Float(precision=53))
        b.alter_column("max_threshold", type_=sa.Float(precision=53))
        b.alter_column("suggested_action", type_=sa.Text())
        b.alter_column("why_priority", type_=sa.Text())
        b.alter_column("status", type_=sa.Text(), server_default="'OPEN'::text")
        b.alter_column("issuer_name", type_=sa.Text())
        b.alter_column("machine_details", type_=postgresql.JSONB())
        b.alter_column("readings_snapshot", type_=postgresql.JSONB())
        b.alter_column("created_at", server_default=sa.text("now()"))

        b.drop_constraint("alerts_equipment_id_fkey", type_="foreignkey")
        b.create_foreign_key(
            "alerts_equipment_id_fkey",
            "equipment",
            ["equipment_id"],
            ["id"],
            ondelete="SET NULL",
        )
        b.drop_constraint("alerts_parameter_id_fkey", type_="foreignkey")
        b.create_foreign_key(
            "alerts_parameter_id_fkey",
            "parameters",
            ["parameter_id"],
            ["id"],
            ondelete="SET NULL",
        )

        # If prior migrations created updated_at, keep it if present but live doesn't have it.
        # We drop it to match live schema.
        try:
            b.drop_column("updated_at")
        except Exception:
            pass

    # user_profiles
    with op.batch_alter_table("user_profiles") as b:
        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        # supabase_user_id is UUID in live, and references auth.users; we align type here.
        b.alter_column("supabase_user_id", type_=uuid, postgresql_using="supabase_user_id::uuid")
        b.alter_column("email", type_=sa.Text())
        b.alter_column("display_name", type_=sa.Text())
        b.alter_column("role", type_=sa.Text(), server_default="'Operator'::text")
        b.alter_column("created_at", server_default=sa.text("now()"))
        b.alter_column("updated_at", server_default=sa.text("now()"))

    # work_orders: live schema differs significantly. We rebuild in place.
    # Drop constraints/indexes that refer to alert_id/legacy columns, then reshape columns.
    with op.batch_alter_table("work_orders") as b:
        for idx in ("ix_work_orders_created_at", "ix_work_orders_priority", "ix_work_orders_status"):
            try:
                b.drop_index(idx)
            except Exception:
                pass
        for ck in ("ck_work_orders_priority", "ck_work_orders_status"):
            try:
                b.drop_constraint(ck, type_="check")
            except Exception:
                pass
        for uq in ("uq_work_orders_alert_id",):
            try:
                b.drop_constraint(uq, type_="unique")
            except Exception:
                pass
        try:
            b.drop_constraint("work_orders_alert_id_fkey", type_="foreignkey")
        except Exception:
            pass

        b.alter_column("id", type_=uuid, postgresql_using="id::uuid")
        # alert_id column is not in live.
        try:
            b.drop_column("alert_id")
        except Exception:
            pass

        # Ensure equipment_id is UUID nullable with SET NULL FK.
        b.alter_column("equipment_id", type_=uuid, postgresql_using="equipment_id::uuid", nullable=True)
        try:
            b.drop_constraint("work_orders_equipment_id_fkey", type_="foreignkey")
        except Exception:
            pass
        b.create_foreign_key(
            "work_orders_equipment_id_fkey",
            "equipment",
            ["equipment_id"],
            ["id"],
            ondelete="SET NULL",
        )

        # title required in live; old schema had description required.
        # If a legacy description exists and title doesn't, create title and relax description.
        try:
            b.add_column(sa.Column("title", sa.Text(), nullable=True))
        except Exception:
            pass
        b.alter_column("description", type_=sa.Text(), nullable=True)

        # status/priority are text defaults in live
        b.alter_column("status", type_=sa.Text(), server_default="'OPEN'::text")
        b.alter_column("priority", type_=sa.Text(), server_default="'MEDIUM'::text")

        # Remove legacy columns not in live
        for col in ("issuer_name", "due_at", "machine_details", "readings_snapshot", "resolution_notes", "root_cause", "closed_at"):
            try:
                b.drop_column(col)
            except Exception:
                pass

        # Ensure assigned_to exists
        try:
            b.add_column(sa.Column("assigned_to", sa.Text(), nullable=True))
        except Exception:
            pass

        # closed_by already exists in our migrations; keep it.
        b.alter_column("closed_by", type_=sa.Text(), nullable=True)

        b.alter_column("created_at", server_default=sa.text("now()"))
        b.alter_column("updated_at", server_default=sa.text("now()"))

    # work_order_part_lines not present in live schema
    try:
        op.drop_table("work_order_part_lines")
    except Exception:
        pass

    # Backfill: ensure work_orders.title is not null by copying from description when needed.
    op.execute(
        sa.text(
            "update work_orders set title = coalesce(title, description, 'Work Order')"
        )
    )
    with op.batch_alter_table("work_orders") as b:
        b.alter_column("title", nullable=False)
        b.create_index("work_orders_status_idx", ["status"])
        b.create_index("work_orders_priority_idx", ["priority"])


def downgrade() -> None:
    """Irreversible reconciliation (live-schema alignment)."""
    raise RuntimeError("Downgrade not supported for live-schema reconciliation.")
