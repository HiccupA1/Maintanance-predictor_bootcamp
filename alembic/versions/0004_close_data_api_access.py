"""Close direct Data API access to application tables (D17).

Revision ID: 0004_close_data_api_access
Revises: 0003_model_registry_risk_scores
Create Date: 2026-11-19

**Problem.** The baseline's RLS policies let every ``authenticated``
Supabase user ``select`` all domain tables and ``insert`` readings through
the auto-generated Data API, using only the public publishable key. That
bypasses the API's role checks (Docs/security/authorization-matrix.md). The
admin policy on ``user_profiles`` likewise allows role changes outside the
audited API.

**Fix.** The frontend uses Supabase for authentication only, and all data
goes through the FastAPI backend. So:

1. Drop every policy on the application tables, and ``is_admin()``. With RLS
   enabled and no policies, the Data API roles see and change nothing.
2. Revoke all table privileges from ``anon`` and ``authenticated`` as a
   second layer, in case RLS is ever disabled by mistake.

**Safety check.** The API must reach these tables through a role that
bypasses RLS (Supabase's ``postgres`` role does). The migration checks the
role it runs as, which is the same ``DATABASE_URL`` the API uses, and
aborts if that role would lose access. That turns a misconfiguration into a
failed deploy instead of an outage.

On plain Postgres (CI, local) the Supabase roles do not exist, and only
step 1 applies.
"""

from __future__ import annotations

from alembic import op

revision = "0004_close_data_api_access"
down_revision = "0003_model_registry_risk_scores"
branch_labels = None
depends_on = None

TABLES = (
    "equipment",
    "parameters",
    "readings",
    "alerts",
    "work_orders",
    "user_profiles",
    "model_versions",
    "risk_scores",
)

POLICIES = (
    ("equipment", "authenticated users can read maintenance data"),
    ("parameters", "authenticated users can read parameters"),
    ("readings", "authenticated users can read readings"),
    ("readings", "authenticated users can submit readings"),
    ("alerts", "authenticated users can read alerts"),
    ("work_orders", "authenticated users can read work orders"),
    ("user_profiles", "users can read own profile"),
    ("user_profiles", "admins can manage profiles"),
)


def upgrade() -> None:
    op.execute("""
        do $check$
        declare
          bypass boolean;
        begin
          select rolsuper or rolbypassrls into bypass
          from pg_roles where rolname = current_user;
          if not bypass and not exists (
            select 1 from pg_tables
            where schemaname = 'public' and tablename = 'equipment'
              and tableowner = current_user
          ) then
            raise exception
              'D17: role % neither bypasses RLS nor owns the tables; '
              'removing the policies would cut the API off. Run migrations '
              'and the API as the postgres role (or grant BYPASSRLS).',
              current_user;
          end if;
        end
        $check$;
        """)
    for table, policy in POLICIES:
        op.execute(f'drop policy if exists "{policy}" on public.{table}')
    op.execute("drop function if exists public.is_admin()")
    tables = ", ".join(f"public.{t}" for t in TABLES)
    op.execute(f"""
        do $revoke$
        begin
          if exists (select 1 from pg_roles where rolname = 'anon') then
            execute 'revoke all on {tables} from anon';
          end if;
          if exists (select 1 from pg_roles where rolname = 'authenticated') then
            execute 'revoke all on {tables} from authenticated';
          end if;
        end
        $revoke$;
        """)


def downgrade() -> None:
    """Restore the baseline grants and policies (re-opens D17)."""
    tables = ", ".join(f"public.{t}" for t in TABLES)
    op.execute(f"""
        do $restore$
        begin
          if to_regnamespace('auth') is null then
            return;
          end if;
          execute 'grant all on {tables} to anon, authenticated';

          create or replace function public.is_admin()
          returns boolean language sql stable security definer
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
        $restore$;
        """)
