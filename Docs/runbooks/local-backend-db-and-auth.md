[CodeWiki](../../../kavia-docs/CodeWiki/index.md) / [Onboarding](../../../kavia-docs/CodeWiki/Onboarding/index.md)

# Local backend DB + Auth troubleshooting (503 `/health/db`, 401 `/v1/me`)

This runbook explains how the FastAPI backend in `Maintanance-predictor_bootcamp/` expects its database and authentication to run locally, and provides copy/paste commands to resolve common errors.

## Symptoms and what they mean

### A) `GET /health/db` returns 503 `dependency_unavailable`
The backend executes a trivial `SELECT 1` using SQLAlchemy. Any connection error (DB not running, wrong host/port, wrong credentials, wrong database name) returns:

- HTTP 503
- `{"detail":"Database is not reachable."}`

This is expected behavior when the DB cannot be reached.

### B) `GET /v1/me` returns 401 even with `Authorization: Bearer ...`
If you send a Bearer token, the backend attempts to validate it as a Supabase access token using:

- RS256 algorithm (asymmetric)
- Supabase JWKS endpoint (`/.well-known/jwks.json`)

If `SUPABASE_URL` is missing (so the backend cannot fetch JWKS), or the token is from a different Supabase project, the backend returns 401.

## 1) How the backend expects the database to run locally

This repository does not include a docker-compose file for the backend. By default, the backend expects a PostgreSQL instance reachable at:

`postgresql+psycopg2://postgres:postgres@localhost:5432/workorders`

You can satisfy that requirement with either Docker (recommended) or a locally installed Postgres service.

### If your database is in Supabase (hosted Postgres)

Set `DATABASE_URL` to your Supabase Postgres connection string (Supabase Dashboard → Project Settings → Database → Connection string).

Example format:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:YOUR_DB_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
```

Then restart the backend and re-check:

```bash
curl -i http://localhost:8000/health/db
curl -i http://localhost:8001/health/db
```

## 2) Start PostgreSQL locally

### Option A (recommended): Docker Postgres (no repo compose required)

```bash
docker run --name workorders-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=workorders \
  -p 5432:5432 \
  -d postgres:16
```

Verify container is running:

```bash
docker ps --filter "name=workorders-postgres"
```

Verify database answers:

```bash
docker exec -it workorders-postgres psql -U postgres -d workorders -c "select 1;"
```

### Option B: Local Postgres service

Ensure Postgres is running on `localhost:5432` and create a database named `workorders`.
Verify connectivity:

```bash
psql "postgresql://postgres:postgres@localhost:5432/workorders" -c "select 1;"
```

## 3) Run backend migrations and start the API

From `Maintanance-predictor_bootcamp/`:

```bash
cd Maintanance-predictor_bootcamp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Set the DB URL:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/workorders"
```

Run Alembic migrations:

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify readiness:

```bash
curl -i http://localhost:8000/health/db
```

Expected:

- HTTP 200
- `{"status":"ok","database":"ok"}`

## 4) Fix `/v1/me` 401 (Supabase token validation)

### Path 1: Real Supabase auth (recommended for production parity)

Configure the backend with your Supabase project URL so it can fetch JWKS:
Supabase Dashboard → Project Settings → API → Project URL

```bash
export SUPABASE_URL="https://YOUR_PROJECT_REF.supabase.co"
export ENABLE_DEV_IDENTITY_SHIM="false"
```

Restart the backend and call:

```bash
curl -i http://localhost:8000/v1/me \
  -H "Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN"
```

If you still see 401:
- Confirm you are using the *access_token* (not refresh token).
- Confirm the token was issued by the same Supabase project whose URL you configured.
- If you configured `SUPABASE_JWT_AUDIENCE`, confirm the token's `aud` matches it.

### Path 2: DEV-only identity shim (no Supabase)

Enable the shim:

```bash
export ENABLE_DEV_IDENTITY_SHIM="true"
```

Call `/v1/me` WITHOUT Authorization, and provide role/name headers:

```bash
curl -i http://localhost:8000/v1/me \
  -H "X-User-Role: PlantManager" \
  -H "X-User-Name: Dev User"
```

Expected HTTP 200 with the dev identity payload.

Note: If your client always sends `Authorization: Bearer ...`, the backend will attempt token validation and may 401 before it can fall back to the DEV shim. For shim testing, do not send Authorization.

## 5) Common quick checks

- Is the API up?

```bash
curl -i http://localhost:8000/health
```

- Is the DB up?

```bash
curl -i http://localhost:8000/health/db
```

- What user do I get?

```bash
curl -i http://localhost:8000/v1/me
```

## 6) Environment variables reference

See:

- `Maintanance-predictor_bootcamp/.env.example`
- `Maintanance-predictor_bootcamp/Docs/runbooks/supabase.md`
