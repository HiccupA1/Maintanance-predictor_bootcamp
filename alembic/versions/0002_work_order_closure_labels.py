"""Work-order closure fields, alert link and failure labels (FR7, FR9, FR10).

Revision ID: 0002_work_order_closure_labels
Revises: 0001_baseline
Create Date: 2026-11-18

Expand-only: every new column is nullable, so the running release is
unaffected. The failure labels (``failure_confirmed``, ``failure_mode``)
are the ground truth for the ML risk model (ADR-0006). ``failure_mode``
mirrors the AI4I 2020 failure modes plus OTHER.
"""

from __future__ import annotations

from alembic import op

revision = "0002_work_order_closure_labels"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        alter table public.work_orders
          add column alert_id uuid
            references public.alerts(id) on delete set null,
          add column resolution_notes text,
          add column root_cause text,
          add column closed_at timestamptz,
          add column failure_confirmed boolean,
          add column failure_mode text,
          add constraint work_orders_failure_mode_check
            check (failure_mode in ('TWF', 'HDF', 'PWF', 'OSF', 'RNF', 'OTHER'));
        create unique index work_orders_alert_id_key
          on public.work_orders(alert_id) where alert_id is not null;
        """)


def downgrade() -> None:
    op.execute("""
        drop index if exists public.work_orders_alert_id_key;
        alter table public.work_orders
          drop constraint if exists work_orders_failure_mode_check,
          drop column if exists failure_mode,
          drop column if exists failure_confirmed,
          drop column if exists closed_at,
          drop column if exists root_cause,
          drop column if exists resolution_notes,
          drop column if exists alert_id;
        """)
