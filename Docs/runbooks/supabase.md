# Supabase (jbloqfbkfwdjvyrzxauz) — Deployment + Live Verification Runbook

This repo currently contains application code and planning docs that reference Supabase (Auth + Postgres, and optionally Edge Functions).

For local development troubleshooting of backend DB connectivity (503 on `/health/db`) and local auth behavior (401 on `/v1/me`), see:

- `Docs/runbooks/local-backend-db-and-auth.md`

## Current status in this workspace (deployment prerequisites)

From live inspection of this environment:

1) **Supabase CLI is not installed**
- `supabase` is not available (`supabase: command not found`)
- Therefore we cannot run: `supabase login`, `supabase link`, `supabase db push`, `supabase functions deploy`, or `supabase functions list`

2) **No Supabase credentials are available to this runtime**
- SupabaseTools cannot see any credentials (`No valid Supabase credentials found...`)
- This blocks live verification via SupabaseTools (list tables, run SQL, etc.)

3) **The migration directory is present**
- `supabase/migrations/20260805000000_domain_schema.sql` is checked into the repository.
- `supabase/config.toml` and `supabase/functions/*` are optional and are not currently required by this database migration.

---

## 0) Required environment variables (MANDATORY)

### For SupabaseTools (this agent runtime)

These names are accepted by the runtime:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- Optional (server-only): `SUPABASE_SECRET_KEY`

After these exist, this agent can:

- list tables
- create missing tables
- run SQL, RLS, policies, and functions
- do live verification queries

> Do **not** expose `SUPABASE_SERVICE_ROLE_KEY` to the frontend.

### For Vite frontend (`Maintanance-predictor_bootcamp/frontend`)

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_API_BASE_URL`
- `VITE_EDGE_FUNCTIONS_BASE_URL` if calling Supabase Edge Functions

### For the FastAPI backend (`Maintanance-predictor_bootcamp/app`)

- `SUPABASE_URL` (used to derive `.../auth/v1/.well-known/jwks.json`)
- Optional: `SUPABASE_JWKS_URL` (explicit override for JWKS endpoint)
- Optional: `SUPABASE_JWT_AUDIENCE` (enable `aud` validation when set)

The backend validates Supabase access tokens using the project JWKS and supports
both `RS256` and `ES256` (EC P-256) signed JWTs.

#### JWKS troubleshooting notes (backend `/v1/me` returns 401)

When the backend returns a 401 complaining about JWKS/signing key resolution, the
most common causes are:

- `SUPABASE_URL` points to the wrong project (JWKS keys won't contain the token `kid`)
- `SUPABASE_URL` is missing `https://` or has a typo (bad derived JWKS URL)
- Network / SSL interception issues prevent fetching `.../.well-known/jwks.json`
- Supabase key rotation happened and the backend needs to refresh JWKS (the API
  caches JWKS for ~5 minutes)

The API now includes safe diagnostics in the 401 detail such as `jwks_url`, `kid`,
and `alg`, and logs the underlying exception with the request correlation id.

---

## 1) Supabase CLI prerequisites

To deploy via Supabase CLI from a repo:

### A) Supabase CLI installed and authenticated

Install Supabase CLI using one of the supported approaches:

**macOS (brew)**

```bash
brew install supabase/tap/supabase
```

**Linux/macOS (npm)**

```bash
npm i -g supabase
```

Then authenticate:

```bash
supabase login
```

### B) Supabase project directory

> **Schema changes no longer go through the Supabase CLI.** Alembic owns the
> schema (ADR-0009, `Docs/runbooks/database-migrations.md`). The former SQL
> migrations are archived under `supabase/archive/` and must not be applied.
> `supabase/migrations/` has been removed on purpose.

A linked project may also include:

```text
supabase/config.toml
supabase/functions/
```

---

## 2) Domain schema, roles, RLS, and initial administrator

The Alembic baseline (`alembic/versions/0001_baseline.py`) creates the following Supabase tables:

- `equipment`
- `parameters`
- `readings`
- `alerts`
- `work_orders`
- `user_profiles`

It also adds indexes, RLS policies, an administrator lookup function, and the default application role behavior.

The `user_profiles` table is the source of truth for application roles. Its canonical columns are:

- `supabase_user_id` — the Supabase Auth user UUID and unique profile key
- `email`
- `display_name`
- `role`

The only valid persisted role values are:

- `Admin`
- `PlantManager`
- `Operator`
- `MaintenanceEngineer`

These names and columns are the contract used by the backend `/v1/admin/users` list endpoint and its role-update endpoint. The admin endpoint identifies users by `supabase_user_id`, not by the internal profile `id`.

Apply schema changes with Alembic, and bootstrap the first Admin with
`scripts/seed_admin.py` and `BOOTSTRAP_ADMIN_EMAIL`. Both are covered in
`Docs/runbooks/database-migrations.md`. No admin account is named in code or
migrations.

Other authenticated users are provisioned as `Operator` on first sign-in. An Admin can review and change their roles from `/admin/users`.

The profile policies allow authenticated users to read their own profile, while only an existing Admin can insert, update, or delete profiles; users cannot promote themselves. The policies on the domain tables are currently too broad (D17).

The API enforces role-based access on every route (`Docs/security/authorization-matrix.md`); the frontend's navigation and route guards only mirror it.

---

## 3) Standard CLI commands (link + deploy)

Run these commands from the repository root where `supabase/` exists.

### Link the repository to the Supabase project

```bash
supabase link --project-ref jbloqfbkfwdjvyrzxauz
```

### Database migrations

Do not use `supabase db push`. See `Docs/runbooks/database-migrations.md`.

### Deploy Edge Functions

List functions in the repository:

```bash
ls -la supabase/functions
```

Deploy an individual function when present:

```bash
supabase functions deploy api
```

### Set Edge Function secrets

```bash
supabase secrets set \
  SUPABASE_URL="https://jbloqfbkfwdjvyrzxauz.supabase.co" \
  SUPABASE_SECRET_KEY="***" \
  ENABLE_DEV_IDENTITY_SHIM="false"
```

---

## 4) Live verification checklist

### A) Verify database connectivity

In the Supabase SQL editor:

```sql
select now();
```

### B) Verify tables exist

Confirm these tables exist:

- `equipment`
- `parameters`
- `readings`
- `alerts`
- `work_orders`
- `user_profiles`

### C) Verify the initial administrator profile

After running `scripts/seed_admin.py`:

```sql
select email, role
from public.user_profiles
where role = 'Admin';
```

Expected role:

```text
Admin
```

### D) Verify schema, roles, and RLS

Confirm the profile shape and canonical role values:

```sql
select column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'user_profiles'
order by ordinal_position;

select distinct role
from public.user_profiles
order by role;
```

Confirm RLS is enabled and the expected policies exist:

```sql
select relname, relrowsecurity
from pg_class
where oid = 'public.user_profiles'::regclass;

select policyname, cmd, roles
from pg_policies
where schemaname = 'public'
  and tablename = 'user_profiles'
order by policyname;
```

`alembic current` should report the expected head, and `alembic check` should report no drift.

### E) Verify Edge Functions

List deployed functions:

```bash
supabase functions list
```

Hit a health endpoint when available:

```bash
curl -i "https://jbloqfbkfwdjvyrzxauz.functions.supabase.co/api/health"
```

If auth-protected routes exist, verify Authorization header behavior using a real Supabase access token.

---

## 5) Auth redirect URL configuration

In Supabase Dashboard:

- Authentication → URL Configuration
  - Site URL: the production frontend base URL
  - Additional Redirect URLs:
    - `http://localhost:3000/**`
    - `https://yourapp.com/**`

---

## What is needed to execute deployment from this workspace

1) Provide the Supabase environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - Optional `SUPABASE_SECRET_KEY`
2) Install and authenticate the Supabase CLI.
3) Link the repository:
   ```bash
   supabase link --project-ref jbloqfbkfwdjvyrzxauz
   ```
4) Apply schema changes with Alembic (`Docs/runbooks/database-migrations.md`).
5) Create or invite the administrator in Supabase Auth, then run `scripts/seed_admin.py`.
6) Verify the Admin profile, domain tables, schema, roles, and RLS policies.
7) Request commit and push approval before pushing to the main branch.

## Runtime readiness blockers

### A) SupabaseTools requires runtime secrets

Live checks require:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- Optional `SUPABASE_SECRET_KEY`

Without these, the runtime reports:

```text
No valid Supabase credentials found in environment variables, project manifest, or .env
```

### B) Alembic migrations require backend `DATABASE_URL`

Running:

```bash
cd Maintanance-predictor_bootcamp
alembic upgrade head
```

attempts to connect to the configured database URL. For Supabase deployment, `DATABASE_URL` must be set to the Supabase Postgres connection string through environment configuration.

### C) Frontend CI Node version

Use Node 20.19+ or Node 22.12+ for the frontend build and test pipeline, or pin the Vite React plugin to a Node-18-compatible version.
