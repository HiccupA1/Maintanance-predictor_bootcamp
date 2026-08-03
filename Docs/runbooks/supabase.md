# Supabase (pirnwbvbiuqfycxtgskt) — Deployment + Live Verification Runbook

This repo currently contains application code and planning docs that reference Supabase (Auth + Postgres, and optionally Edge Functions).

## Current status in this workspace (BLOCKERS)
From live inspection of this environment:

1) **Supabase CLI is not installed**
- `supabase` is not available (`supabase: command not found`)
- Therefore we cannot run: `supabase login`, `supabase link`, `supabase db push`, `supabase functions deploy`, or `supabase functions list`

2) **No Supabase credentials are available to this runtime**
- SupabaseTools cannot see any credentials (`No valid Supabase credentials found...`)
- This blocks live verification via SupabaseTools (list tables, run SQL, etc.)

3) **No `supabase/` project directory exists in the repo root**
- `supabase/config.toml`, `supabase/migrations/*`, and `supabase/functions/*` are not present
- Therefore, even with the CLI, there is **nothing in-repo to deploy** yet

---

## 0) Required environment variables (MANDATORY)

### For SupabaseTools (this agent runtime)
These names are accepted by the runtime:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (or `SUPABASE_KEY`)
- (optional but recommended for admin SQL/migrations) `SUPABASE_SERVICE_ROLE_KEY`

After these exist, this agent can:
- list tables
- create missing tables
- run SQL (RLS/policies/functions)
- do live verification queries

> Do NOT expose `SUPABASE_SERVICE_ROLE_KEY` to the frontend.

### For Vite frontend (`Maintanance-predictor_bootcamp/frontend`)
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL` (if calling a separate backend)
- `VITE_EDGE_FUNCTIONS_BASE_URL` (if calling Supabase Edge Functions; if your code uses a different var name, keep consistent)

---

## 1) Supabase CLI prerequisites (repo + environment)

To deploy via Supabase CLI from a repo, you generally need:

### A) Supabase CLI installed and authenticated
Install Supabase CLI (choose one):

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

### B) A `supabase/` directory in the repo root (or working directory)
Expected layout:
- `supabase/config.toml`
- `supabase/migrations/*` (SQL migrations) and/or
- `supabase/functions/*` (Edge Functions)

If you intend to deploy Edge Functions/migrations from this repo, create/commit the `supabase/` directory.

---

## 2) Standard CLI commands (link + deploy)

> Run these from the repo root (where `supabase/` exists).

### Link the repo to the Supabase project
```bash
supabase link --project-ref pirnwbvbiuqfycxtgskt
```

### Push DB migrations (if using supabase migrations)
```bash
supabase db push
```

### Deploy Edge Functions (if present)
List functions in repo:
```bash
ls -la supabase/functions
```

Deploy all (example deploying one function):
```bash
supabase functions deploy api
# or:
# supabase functions deploy <function_name>
```

### Set Edge Function secrets (if using functions)
```bash
supabase secrets set \
  SUPABASE_URL="https://pirnwbvbiuqfycxtgskt.supabase.co" \
  SUPABASE_SERVICE_ROLE_KEY="***" \
  ENABLE_DEV_IDENTITY_SHIM="false"
```

---

## 3) Live verification checklist (post-deploy)

### A) Verify DB connectivity
In Supabase SQL editor:
```sql
select now();
```

### B) Verify tables exist
Confirm domain tables exist (expected examples from this project’s design):
- `equipment`
- `parameters`
- `readings`
- `alerts`
- `work_orders`
- `work_order_part_lines`
- `user_profiles` (or equivalent user/role persistence table)

### C) Verify Edge Functions are deployed and reachable
List deployed functions:
```bash
supabase functions list
```

Hit a health endpoint (example):
```bash
curl -i "https://pirnwbvbiuqfycxtgskt.functions.supabase.co/api/health"
```

If auth-protected routes exist, verify Authorization header behavior using a real Supabase access token.

---

## 4) Auth redirect URL configuration (required for email links/OAuth)
In Supabase Dashboard:
- Authentication → URL Configuration
  - Site URL: your production frontend base URL (e.g., `https://yourapp.com`)
  - Additional Redirect URLs:
    - `http://localhost:3000/**` (or your Vite dev URL)
    - `https://yourapp.com/**`

---

## What’s needed next (so deployment can be executed from this workspace)
1) Ensure the container has Supabase env vars (`SUPABASE_URL`, `SUPABASE_ANON_KEY`/`SUPABASE_KEY`, optionally `SUPABASE_SERVICE_ROLE_KEY`)
2) Install Supabase CLI in this environment
3) Add/commit a `supabase/` directory (migrations/functions) if you expect deployment artifacts from this repo
4) Re-run:
   - `supabase link --project-ref pirnwbvbiuqfycxtgskt`
   - `supabase db push`
   - `supabase functions deploy ...`
   - `supabase functions list` + curl smoke call

## Step 3 readiness blockers observed in CI/runtime (important)

### A) SupabaseTools requires runtime secrets
This agent runtime can only perform live checks (list tables / run SQL / create tables) when ALL required env vars exist:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (or `SUPABASE_KEY`)
- optional (admin SQL/migrations): `SUPABASE_SERVICE_ROLE_KEY`

Without these, SupabaseTools errors with:
`No valid Supabase credentials found in environment variables, project manifest, or .env`.

### B) Alembic migrations require backend DATABASE_URL
Running:
`cd Maintanance-predictor_bootcamp && alembic upgrade head`
will attempt localhost Postgres unless `DATABASE_URL` is set to the Supabase Postgres connection string.

### C) Frontend CI Node version requirement
`@vitejs/plugin-react@5.2.0` declares Node engines:
`^20.19.0 || >=22.12.0`

If your CI/runtime is Node 18, you may see EBADENGINE warnings and unstable Vitest/Vite behavior.
Recommendation:
- Use Node 20.19+ (or 22.12+) for frontend build/test pipelines, OR pin plugin-react to a Node-18-compatible version.
