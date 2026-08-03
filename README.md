# Work Order Management Backend

FastAPI + PostgreSQL + SQLAlchemy 2.x + Alembic backend implementing the
**API Contract — Case (Work Order) Management v0.2**.

Authentication is intentionally **not** enforced in this stage, but the code is
layered (router → service → repository → models) so auth can be added later
(e.g., a shared dependency injected on the routers).

`GET /v1/me` is a development-only identity shim. It defaults to
`{"user_id":"dev","name":"Dev User","role":"PlantManager"}` and accepts
`X-User-Role` (`Admin`, `PlantManager`, `Operator`, or `MaintenanceEngineer`)
plus optional `X-User-Name`. This is not authentication and must not be treated
as secure authorization.

## Implemented endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/alerts/{alert_id}/work-orders` | Create a work order from an alert |
| PUT | `/v1/work-orders/{work_order_id}` | Update a work order |
| GET | `/v1/work-orders/{work_order_id}` | Fetch a work order by id |
| GET | `/v1/work-orders` | List work orders (filter + paginate) |
| GET | `/v1/me` | Development identity/RBAC shim |
| GET | `/v1/equipment` | List equipment |
| POST | `/v1/equipment` | Create equipment |
| GET | `/v1/equipment/{equipment_id}` | Fetch equipment |
| PUT | `/v1/equipment/{equipment_id}` | Update equipment |
| GET | `/v1/equipment/{equipment_id}/parameters` | List parameters |
| POST | `/v1/equipment/{equipment_id}/parameters` | Create parameter |
| PUT | `/v1/parameters/{parameter_id}` | Update thresholds |
| POST | `/v1/readings` | Record reading and evaluate alerts |
| GET | `/v1/equipment/{equipment_id}/parameters/{parameter_id}/readings` | Reading history |
| PUT | `/v1/readings/{reading_id}` | Edit reading within five minutes |
| GET | `/v1/alerts` | List alerts |
| GET | `/v1/alerts/{alert_id}` | Alert detail |
| GET | `/health` | Liveness probe (`{"status":"ok"}`) |
| GET | `/health/db` | DB readiness (`SELECT 1`) |

OpenAPI/Swagger UI is available at `/docs` and the raw schema at `/openapi.json`.

## MVP API contract summary

- `GET /v1/me`: returns `user_id`, `name`, and `role`; headers
  `X-User-Role` and `X-User-Name` are development-only overrides.
- Equipment create/update requires `equipment_id`, `name`, `location`, `type`,
  and integer `criticality` from 1 through 5.
- Parameter create/update requires `name`, `unit`, boolean `active`, and at
  least one of `min_threshold` or `max_threshold`.
- `POST /v1/readings` accepts string `value`, equipment and parameter ids, and
  an optional timestamp. Numeric threshold breaches create or update one active
  alert; recovery resolves it. Inactive parameters and non-numeric values do
  not evaluate alerts.
- Reading edits require `value` and `modification_reason` and are limited to
  five minutes after the original timestamp.
- Closing a work order requires `resolution_notes`, `root_cause`, and at least
  one part line. Use `part_name: "N/A"` when no part was used. Closure sets the
  source alert to `RESOLVED` and updates equipment `last_service_date`.

## Project structure

```text
app/
  main.py
  api/v1/
    api.py
    routers/
      health.py
      me.py
      domain.py
      work_orders.py
  core/
    config.py
    logging.py
    errors.py
  db/
    base.py
    session.py
  models/
    alert.py
    equipment.py
    work_order.py
    work_order_part_line.py
  schemas/
    common.py
    domain.py
    work_orders.py
  repositories/
    alerts.py
    work_orders.py
  services/
    domain.py
    work_orders.py
tests/
  conftest.py
  test_health.py
  test_work_orders.py
alembic/
  versions/
    0001_initial.py
    0002_normalize_work_order_enums.py
    0003_mvp_domains.py
```

## Error model

Every error returns `application/problem+json` with exactly these fields:
`type`, `title`, `status`, `detail`, `instance`, `code`, `correlation_id`,
and `errors[]` (each item: `field`, `message`, `rule`, `expected`).

Standard `code` values include `unauthorized`, `forbidden`,
`alert_not_found`, `work_order_not_found`, `duplicate_work_order`,
`invalid_state`, `invalid_request`, `dependency_unavailable`,
`internal_error`, and `data_integrity_error`.

## Business rules enforced

- **One work order per alert** — a duplicate returns
  `409 duplicate_work_order`.
- **Alert existence** — creating against an unknown alert returns
  `404 alert_not_found`.
- **Single transaction create** — work-order insertion and alert transition to
  `IN_PROGRESS` commit atomically.
- **No-op update rejected** — an empty update body returns
  `422 invalid_request`.
- **Closed work orders are immutable** — updating a closed work order returns
  `409 invalid_state`.
- **Closure requirements** — closing requires resolution notes, root cause, and
  at least one part line.
- **Alert/equipment closure side effects** — closing resolves the source alert
  and updates equipment's last service date.
- **Enums are uppercase and constrained** — priority
  `{CRITICAL,HIGH,MEDIUM}`, status `{OPEN,CLOSED}`.
- **Reading alert lifecycle** — inclusive threshold boundaries use
  `value <= min_threshold` or `value >= max_threshold`; one active alert is
  reused until resolved.

## Runbook

### Supabase deployment + verification

See: `Docs/runbooks/supabase.md`

### 1. Install dependencies

```bash
cd Maintanance-predictor_bootcamp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Set the database URL

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/workorders"
```

> The real `.env` is managed by the orchestrator/deployment. See `.env.example`
> for the full list of variables. Do not commit secrets.

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Seed sample work-order data

From `Maintanance-predictor_bootcamp`:

```bash
python scripts/seed_sample_data.py
```

On Windows:

```powershell
py scripts\seed_sample_data.py
```

The repository-root wrapper also supports running `py scripts\seed_sample_data.py`
from the parent directory. The seed entrypoint resolves the backend project
directory before importing `app`, and the backend configuration loads the
project-local `.env`, so the seed uses the same `DATABASE_URL` as the API.

### 4. Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run the tests

```bash
pytest -q
```

Tests use an in-memory SQLite database configured in `tests/conftest.py`, so no
PostgreSQL instance is required for the test suite.
