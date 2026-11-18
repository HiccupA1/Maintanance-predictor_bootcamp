# ADR-0009 — Alembic owns the database schema

- **Status:** Accepted (2026-11-18). The live adoption step (`alembic stamp`) is pending owner approval.
- **Supersedes:** the dual Alembic and `supabase/migrations` arrangement.

## Context

Two tools both claimed to own the schema, and neither could reproduce it:

- **Alembic** (`0002`–`0006`): the chain could not build an empty database
  (D5). Revision `0001` had been deleted, and `0006` was written afterwards
  to match whatever the live database had become.
- **Supabase SQL** (`supabase/migrations`, applied with `supabase db push`):
  this is what actually built the live schema, including RLS. However, the
  ORM models had drifted from it: timestamps without time zones, different
  index names, and an index that does not exist in the database.

As a result, no environment could be built reproducibly, CI could not check
migrations, and the next schema change (FR9–FR10 closure fields, then
telemetry in WP2) had no safe path to production.

## Decision

1. **Alembic is the single source of truth** for the `public` schema. A new
   baseline, `0001_baseline`, reproduces the live schema exactly, apart from
   one change: the hard-coded admin grant moved to `scripts/seed_admin.py`
   (D16).
2. **The baseline also builds Supabase-only objects** (the `auth.users`
   foreign key, RLS policies and `is_admin()`), but only when the `auth`
   schema exists. The same migration therefore runs on plain Postgres in CI
   and in local development.
3. **The old chain and the Supabase SQL are archived, not deleted**, in
   `alembic/archive/` and `supabase/archive/`. `supabase/migrations/` is
   removed, so the Supabase CLI and GitHub integration cannot apply DDL.
4. **The ORM models match the baseline**, and `alembic check` enforces this
   in CI. References into Supabase-managed schemas are excluded from that
   comparison.
5. **The live database is adopted with `alembic stamp 0001_baseline`**,
   which writes metadata only. A clean schema diff against live is required
   first (`Docs/runbooks/database-migrations.md`).

## Alternatives considered

- **Supabase CLI as the owner, with Alembic removed.** This fits RLS
  natively, but it gives no check that the models match the database. It
  also ties every schema change to the Supabase CLI and a linked project,
  which this team's environment cannot run (see `Docs/runbooks/supabase.md`).
  And it weakens the portability that ADR-0008 relies on (migrations shipping
  in the API image to any managed Postgres).
- **Repairing the existing chain.** Reconstructing the missing `0001` would
  produce history that never actually ran anywhere, and `0006` already
  encodes "whatever live was". A baseline that states the schema plainly is
  more honest and easier to review.

## Consequences

- Fresh environments (CI, local, client staging) build with
  `alembic upgrade head`, and CI blocks on migration errors and model drift.
- Every future change, including the D17 RLS tightening, is a reviewed
  Alembic revision with a downgrade, rolled out to staging before production.
- RLS policies and functions are not covered by autogenerate, so they must
  be written as explicit `op.execute` steps. The review checklist in the
  runbook covers this.
- **Pending:** the one-time live stamp needs owner approval and a clean diff
  against the dump of the live database.
