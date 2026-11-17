# Backend Defect Log

| ID | Severity | Description | Status |
|---|---|---|---|
| D1 | P0 | Historical branch contained malformed router package content and missing `/v1` wiring. | Must verify in current main |
| D2 | P2 | Historical pagination ceiling was 100 instead of contract value 200. | Validation fix recorded |
| D3 | P3 | Empty update error may lack a field pointer. | Open improvement |
| D4 | P1 | Retest observed HTTP 500 for valid `page_size=200`. | Open; requires logs and regression test |
| D5 | P1 | Alembic chain cannot build a fresh database. Revision `0001` was deleted in `a1c136e`, and `0002` (`down_revision = None`) alters a `work_orders` table that no migration creates. `0006` also passes Postgres-introspected strings (`"''::text"`) as `server_default`, which render as quoted literals. CI job `migrations` runs `alembic upgrade head` on an empty Postgres and is non-blocking until this is fixed. | Open |
| D6 | P2 | Health probes are served at `/v1/health` and `/v1/health/db` (matching `Docs/stage-3/API-contract.md`). The frontend (`frontend/src/api/health.ts`), the smoke tests (`Docs/stage-8/smoke-tests.md`) and `tests/test_health.py` call unversioned `/health`, which returns 404. | Open; quarantined |
| D7 | P1 | `GET /v1/admin/users` with no credentials returns 403 instead of 401: the admin guard resolves the user through the dev identity fallback in `routers/me.py`. Related: user routes without any guard (see CR-001 §3). | Open; quarantined |
| D8 | P1 | Alert responses fail to serialise. UUID coercion receives a non-string value (`AttributeError: 'float' object has no attribute 'replace'`), and `AlertResponse` reads `updated_at`, which the reconciled `alerts` table no longer has. Affects `GET /v1/alerts`. | Open; quarantined |
| D9 | P1 | The work-order test suite targets the pre-reconciliation contract (`POST /v1/alerts/{id}/work-orders`, persisted `alert_id`, DB `CHECK` constraints on enums), which migration `0006` removed. Each test needs triage: either the test is stale, or the behaviour is a lost requirement (PRD FR7, FR9–FR10). | Open; quarantined (13 tests) |
| D10 | P2 | Frontend tests fail. `AppRoutes.test.tsx` (4) cannot find route headings. `AlertsListPage.test.tsx` (1) cannot find the alert link. `WorkOrderDetailPage.test.tsx` (2) finds duplicate text. The likely cause is test drift after auth-gated routing and spare-parts removal; to be confirmed. | Open; quarantined with `it.fails` |
| D11 | P3 | `RequireAuth` and `AuthIndexRedirect` call hooks after an early `BYPASS_AUTH` return, which violates the rules of hooks. Hook order is stable only because `BYPASS_AUTH` is a build-time constant. Also, `VITE_BYPASS_AUTH` must be verified as off in production builds. | Open; lint suppressed per line |
| D12 | P1 | `npm ci` reports 29 vulnerabilities (2 critical, 16 high, 11 moderate) as of 2026-11-18. `Docs/stage-6/frontend-quality-report.md` recorded 7. CI job `security` is non-blocking until this is fixed. | Open |
| D13 | P1 | `pip-audit` reports 34 known vulnerabilities in 5 Python packages (2026-11-18). Runtime: `pyjwt 2.7.0` (14, used for JWT verification), `cryptography 41.0.7` (9), `starlette 0.45.3` (7, via FastAPI). Dev only: `black` (3), `pytest` (1). Upgrades need regression testing of JWT verification. CI job `security` is non-blocking until this is fixed. | Open |
| D14 | P2 | `enable_dev_identity_shim` defaults to `True` in `app/core/config.py`, so a deployment that omits the variable runs with the dev identity fallback. It should default to off and be allowed only when `ENV=dev` (PRD addendum NFR-S1). | Open |

## Quarantine policy

- Backend failures are listed in `tests/known_failures.py` and run as **strict** xfails. Frontend
  failures use `it.fails`. In both cases, a newly failing test fails CI, and a quarantined test
  that starts passing also fails CI until its quarantine entry is removed.
- Every quarantine entry must reference an open row in this log. Closing a defect means
  removing its entries in the same pull request.
- Non-blocking CI jobs (D5, D12) must be made blocking in the pull request that fixes them.
