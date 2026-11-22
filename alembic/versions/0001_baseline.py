"""Baseline schema: the deployed Supabase ``public`` schema as of 2026-11-18.

Revision ID: 0001_baseline
Revises: (none)
Create Date: 2026-11-18

This replaces the broken 0002-0006 chain (D5) and the parallel
``supabase/migrations`` SQL, both now archived. See ADR-0009.

The DDL reproduces what ``supabase/migrations/20260805000000_domain_schema.sql``
and ``20260807000001_alert_context_columns.sql`` built in the live project,
without the admin seed (moved to ``scripts/seed_admin.py``):

- On an empty database, ``alembic upgrade head`` builds the full schema.
- On the live database, which already has this schema, run
  ``alembic stamp 0001_baseline`` once instead. See
  ``Docs/runbooks/database-migrations.md``, which first requires a schema
  diff against live.

Supabase-only objects (the ``auth.users`` foreign key, RLS policies for the
``authenticated`` role, and ``is_admin()``) are created only when the
``auth`` schema exists, so the same migration runs on plain Postgres in CI
and in local development.
"""

from __future__ import annotations

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


TABLES = """
create extension if not exists "pgcrypto";

create table public.equipment (
  id uuid primary key default gen_random_uuid(),
  equipment_id text unique not null,
  name text not null,
  location text not null default '',
  type text not null default '',
  criticality integer not null default 1,
  last_service_date timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.parameters (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid not null
    references public.equipment(id) on delete cascade,
  name text not null,
  unit text not null default '',
  min_threshold double precision,
  max_threshold double precision,
  active boolean not null default true,
  suggested_action text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.readings (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid not null
    references public.equipment(id) on delete cascade,
  parameter_id uuid not null
    references public.parameters(id) on delete cascade,
  value text not null,
  timestamp timestamptz not null default now(),
  entered_by text not null default 'dev',
  modified_by text,
  modified_at timestamptz,
  modification_reason text
);

create table public.alerts (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid references public.equipment(id) on delete set null,
  parameter_id uuid references public.parameters(id) on delete set null,
  priority text not null default 'MEDIUM',
  current_value text,
  breach_timestamp timestamptz,
  min_threshold double precision,
  max_threshold double precision,
  suggested_action text,
  why_priority text,
  status text not null default 'OPEN',
  created_at timestamptz not null default now(),
  issuer_name text,
  machine_details jsonb,
  readings_snapshot jsonb
);

create table public.work_orders (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid references public.equipment(id) on delete set null,
  title text not null,
  description text,
  status text not null default 'OPEN',
  priority text not null default 'MEDIUM',
  assigned_to text,
  closed_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.user_profiles (
  id uuid primary key default gen_random_uuid(),
  supabase_user_id uuid unique not null,
  email text,
  display_name text,
  role text not null default 'Operator',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_profiles_role_check
    check (role in ('Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer'))
);

create index parameters_equipment_id_idx on public.parameters(equipment_id);
create index readings_parameter_id_idx on public.readings(parameter_id);
create index readings_timestamp_idx on public.readings(timestamp desc);
create index alerts_status_idx on public.alerts(status);
create index work_orders_status_idx on public.work_orders(status);
create index user_profiles_role_idx on public.user_profiles(role);

alter table public.equipment enable row level security;
alter table public.parameters enable row level security;
alter table public.readings enable row level security;
alter table public.alerts enable row level security;
alter table public.work_orders enable row level security;
alter table public.user_profiles enable row level security;
"""

# Reproduces the live policies verbatim. Their breadth is tracked as D17
# (authenticated users can read all tables and insert readings through the
# Supabase Data API, bypassing API authorization); the fix is a follow-up
# migration, not a baseline change.
SUPABASE_ONLY = """
do $supabase$
begin
  if to_regnamespace('auth') is null then
    raise notice 'auth schema not found: skipping Supabase-only objects';
    return;
  end if;

  alter table public.user_profiles
    add constraint user_profiles_supabase_user_id_fkey
    foreign key (supabase_user_id) references auth.users(id)
    on delete cascade;

  create or replace function public.is_admin()
  returns boolean
  language sql
  stable
  security definer
  set search_path = public
  as $fn$
    select exists (
      select 1 from public.user_profiles
      where supabase_user_id = auth.uid() and role = 'Admin'
    );
  $fn$;

  create policy "authenticated users can read maintenance data"
    on public.equipment for select to authenticated using (true);
  create policy "authenticated users can read parameters"
    on public.parameters for select to authenticated using (true);
  create policy "authenticated users can read readings"
    on public.readings for select to authenticated using (true);
  create policy "authenticated users can submit readings"
    on public.readings for insert to authenticated with check (true);
  create policy "authenticated users can read alerts"
    on public.alerts for select to authenticated using (true);
  create policy "authenticated users can read work orders"
    on public.work_orders for select to authenticated using (true);
  create policy "users can read own profile"
    on public.user_profiles for select to authenticated
    using (public.is_admin() or supabase_user_id = auth.uid());
  create policy "admins can manage profiles"
    on public.user_profiles for all to authenticated
    using (public.is_admin()) with check (public.is_admin());
end
$supabase$;
"""


def upgrade() -> None:
    """Create the baseline schema."""
    op.execute(TABLES)
    op.execute(SUPABASE_ONLY)


def downgrade() -> None:
    """Drop the baseline schema. Never run this against a live database."""
    op.execute("""
        drop table if exists public.work_orders;
        drop table if exists public.alerts;
        drop table if exists public.readings;
        drop table if exists public.parameters;
        drop table if exists public.user_profiles;
        drop table if exists public.equipment;
        -- After the tables: their policies depend on it.
        drop function if exists public.is_admin();
        """)
