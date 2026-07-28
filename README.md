# Work Order Management Backend

FastAPI + PostgreSQL + SQLAlchemy 2.x + Alembic backend implementing the
**API Contract — Case (Work Order) Management v0.2**.

Authentication is intentionally **not** enforced in this stage, but the code is
layered (router → service → repository → models) so auth can be added later
(e.g., a shared dependency injected on the routers).

## Implemented endpoints

| Method | Path                                    | Description                          |
|--------|-----------------------------------------|--------------------------------------|
| POST   | `/v1/alerts/{alert_id}/work-orders`     | Create a work order from an alert    |
| PUT    | `/v1/work-orders/{work_order_id}`       | Update a work order                  |
| GET    | `/v1/work-orders/{work_order_id}`       | Fetch a work order by id             |
| GET    | `/v1/work-orders`                       | List work orders (filter + paginate) |
| GET    | `/health`                               | Liveness probe (`{"status":"ok"}`)   |
| GET    | `/health/db`                            | DB readiness (`SELECT 1`)            |

OpenAPI/Swagger UI is available at `/docs` and the raw schema at `/openapi.json`.

## Project structure

```text
app/
  main.py                      # FastAPI app, middleware, handler + router wiring
  api/v1/
    api.py                     # router aggregation (/health, /v1/...)
    routers/
      health.py                # health + db readiness
      work_orders.py           # 4 contract endpoints
  core/
    config.py                  # env-driven settings (pydantic-settings)
    logging.py                 # structured logging + correlation id
    errors.py                  # RFC7807 Problem model, codes, handlers
  db/
    base.py                    # declarative Base + JSON/JSONB type
    session.py                 # engine/session + get_db dependency
  models/
    alert.py                   # minimal Alert (MVP stub)
    work_order.py              # WorkOrder (unique alert_id)
    work_order_part_line.py    # spare-part line
  schemas/
    common.py                  # Priority / WorkOrderStatus enums
    work_orders.py             # request/response schemas
  repositories/
    alerts.py                  # alert data access
    work_orders.py             # work order data access + list/filter
  services/
    work_orders.py             # business rules + transactions
tests/
  conftest.py                  # in-memory SQLite + seeded alerts + TestClient
  test_work_orders.py          # happy + negative path tests
  test_health.py               # health endpoint tests
alembic/
  env.py                       # migration environment (uses app settings)
  versions/0001_initial.py     # initial schema
pyproject.toml                 # deps + ruff/black/pytest config
Makefile                       # run/test/lint/format/migrate targets
README.md
.env.example
```

## Error model (RFC7807-like)

Every error returns `application/problem+json` with exactly these fields:
`type`, `title`, `status`, `detail`, `instance`, `code`, `correlation_id`,
and `errors[]` (each item: `field`, `message`, `rule`, `expected`).

Standard `code` values: `unauthorized`, `forbidden`, `alert_not_found`,
`work_order_not_found`, `duplicate_work_order`, `invalid_state`,
`invalid_request`, `dependency_unavailable`, `internal_error`.

## Business rules enforced

- **One work order per alert** — a duplicate returns `409 duplicate_work_order`
  (also enforced by a unique DB constraint on `work_orders.alert_id`).
- **Alert existence** — creating against an unknown alert returns
  `404 alert_not_found`.
- **Single transaction create** — the work order insert and the alert
  transition to `IN_PROGRESS` commit atomically.
- **No-op update rejected** — an empty update body returns
  `422 invalid_request`.
- **Closed work orders are immutable** — updating a `CLOSED` work order returns
  `409 invalid_state`.
- **Enums are uppercase & constrained** — priority `{CRITICAL,HIGH,MEDIUM}`,
  status `{OPEN,CLOSED}`.
- **List validation** — `page >= 1`, `1 <= page_size <= 200`, and
  `created_from <= created_to`.
- **Field names match the contract** (e.g., `due_at`).

## Runbook

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
# or: make migrate
```

### 4. Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# or: make run
```

### 5. Run the tests

```bash
pytest
# or: make test
```

Tests use an **in-memory SQLite** database (`DATABASE_URL=sqlite://`) configured
in `tests/conftest.py`, so no PostgreSQL instance is required to run them. The
`JSONType` column maps to `JSONB` on PostgreSQL and generic `JSON` on SQLite, so
JSON snapshot fields work under both engines.

To run tests against a **PostgreSQL** test database instead:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/workorders_test"
pytest
```

## Assumptions

- **Contract text**: the attachment's contract placeholder was not populated in
  this snapshot; binding requirements were taken from the explicit user
  instructions (endpoints, enums, error model, validations, transaction and
  alert-transition rules). No behavior beyond those instructions was invented.
- **Alert model is an MVP stub** with only the fields needed for the work order
  flow (`id`, `equipment_id`, `status`, `issuer_name`, `machine_details`,
  `readings_snapshot`, timestamps). Alert lifecycle values used here are
  `NEW → IN_PROGRESS → RESOLVED`.
- **UUIDs are stored as strings** (`String(36)`) for portability between
  PostgreSQL and the SQLite test database.
- **Auth is off**; `unauthorized`/`forbidden` exist as structural placeholders
  in the error model for future use.
- **Spare-part lines** have no quantity field (MVP), only `part_name`, `used`,
  and free-text `notes`.

## Commit plan (do NOT run until you say "GO")

```bash
cd Maintanance-predictor_bootcamp
git add -A
git commit -m "feat(backend): Stage 4 Work Order Management API (contract v0.2)

- FastAPI layered backend (router -> service -> repository -> models)
- Endpoints: create/update/get/list work orders + health probes
- RFC7807 error model, standard codes, and validation rules
- SQLAlchemy 2.x models + Alembic initial migration
- One-work-order-per-alert + single-transaction create with alert transition
- pyproject, Makefile, README runbook, and >=5 unit tests"
```
</parameter>
