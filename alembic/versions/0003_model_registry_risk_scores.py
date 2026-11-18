"""Model registry, risk scores, alert source and feature mapping (WP4).

Revision ID: 0003_model_registry_risk_scores
Revises: 0002_work_order_closure_labels
Create Date: 2026-11-19

Expand-only (all additions are nullable or defaulted):

- ``model_versions``: the registry (ADR-0007). ``stage`` is one of shadow
  (scores are stored but never shown), active (raises MODEL alerts) or
  retired. At most one active version per (kind, asset_class).
- ``risk_scores``: every score written, including shadow scores, kept for
  shadow evaluation and drift analysis (WP5). Unpartitioned for now;
  partition it like telemetry once volume warrants (ADR-0003).
- ``alerts.source``: THRESHOLD (default, existing behaviour) or MODEL.
- ``equipment.asset_class``: which model family applies, if any.
- ``parameters.feature_key``: maps a parameter onto a model raw input
  (e.g. ``torque_nm``), so scoring needs no per-asset code.
"""

from __future__ import annotations

from alembic import op

revision = "0003_model_registry_risk_scores"
down_revision = "0002_work_order_closure_labels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table public.model_versions (
          id uuid primary key default gen_random_uuid(),
          version text not null unique,
          kind text not null default 'failure_risk',
          asset_class text not null,
          stage text not null default 'shadow',
          threshold double precision not null,
          features jsonb not null,
          metrics jsonb,
          artifact_uri text not null,
          artifact_sha256 text not null,
          created_at timestamptz not null default now(),
          stage_changed_at timestamptz,
          stage_changed_by text,
          constraint model_versions_stage_check
            check (stage in ('shadow', 'active', 'retired')),
          constraint model_versions_kind_check
            check (kind in ('failure_risk', 'anomaly'))
        );
        create unique index model_versions_one_active
          on public.model_versions(kind, asset_class)
          where stage = 'active';

        create table public.risk_scores (
          id uuid primary key default gen_random_uuid(),
          equipment_id uuid not null
            references public.equipment(id) on delete cascade,
          model_version_id uuid not null
            references public.model_versions(id) on delete cascade,
          score double precision not null,
          flagged boolean not null,
          stage text not null,
          features jsonb not null,
          scored_at timestamptz not null default now()
        );
        create index risk_scores_equipment_scored_idx
          on public.risk_scores(equipment_id, scored_at desc);

        alter table public.alerts
          add column source text not null default 'THRESHOLD',
          add constraint alerts_source_check
            check (source in ('THRESHOLD', 'MODEL'));
        alter table public.equipment add column asset_class text;
        alter table public.parameters add column feature_key text;

        alter table public.model_versions enable row level security;
        alter table public.risk_scores enable row level security;
        """)


def downgrade() -> None:
    op.execute("""
        alter table public.parameters drop column if exists feature_key;
        alter table public.equipment drop column if exists asset_class;
        alter table public.alerts
          drop constraint if exists alerts_source_check,
          drop column if exists source;
        drop table if exists public.risk_scores;
        drop table if exists public.model_versions;
        """)
