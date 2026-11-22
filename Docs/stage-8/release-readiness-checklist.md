# Release Readiness Checklist: v0.3.0

**Status: NOT YET GO.** All engineering gates pass in CI. The remaining items
are environment and owner actions, marked ⏳.

| # | Gate | Status | Evidence |
|---|---|---|---|
| 1 | Backend tests pass | ✅ | CI `Backend tests`: 237 passed, 15 quarantined as strict xfail (D8 ×2, D9 ×13) |
| 2 | Authorization enforced on every route | ✅ | `tests/test_authorization.py`, with completeness checked against the OpenAPI schema |
| 3 | Frontend lint, typecheck, tests and build | ✅ | CI `Frontend`: 59 passed, 7 quarantined (D10) |
| 4 | Migrations build an empty database, show no model drift and round-trip | ✅ | CI `Migrations (Postgres)`, plain and Supabase-stub paths |
| 5 | No direct Data API access (D17) | ✅ in CI · ⏳ on live | `tests/sql/assert_no_data_api_access.sql` |
| 6 | Dependency and image scans clean | ✅ | CI `Dependency audit` (bandit, pip-audit, npm audit) and `Docker image` (Trivy) |
| 7 | Container builds, migrates, starts and runs as non-root | ✅ | CI `Docker image` |
| 8 | Performance targets met at 3× load | ✅ | `Docs/stage-9/performance-report.md`. 75 users: p95 102 ms, 0 errors |
| 9 | ML pipeline reproducible, with an honest model card | ✅ | CI `ML golden retrain`; `ml/model_cards/ai4i-v1.md` |
| 10 | Security review complete; residual risks accepted | ✅ · ⏳ owner sign-off | `Docs/security/security-review.md` (R-1 to R-6) |
| 11 | No open P0/P1 defects | ✅ · ⏳ | D4, D5, D7 and D17 fixed. **D8 (P1)** remains: an alert-serialisation test drift on SQLite. `GET /alerts` works on Postgres under load (performance report), but it must be triaged and closed or downgraded before go-live. **D9** is stale tests, under triage |
| 12 | Live schema diff clean, then `alembic stamp 0001_baseline` | ⏳ | `Docs/runbooks/database-migrations.md` |
| 13 | Migrations 0002 to 0004 applied: staging, then production | ⏳ | same runbook |
| 14 | Smoke tests pass on staging and production | ⏳ | `smoke-tests.md` |
| 15 | Production configuration set: secrets in the store, `CORS_ORIGINS`, `APP_ENV=production`, edge rate limit | ⏳ | security review, "Before go-live" |
| 16 | Branch protection requires **CI OK** | ⏳ | `Docs/runbooks/ci.md` |
| 17 | Client decisions recorded | ⏳ | Authorization-matrix questions (Admin work-order edit, parameter ownership, deletion); recall floor and promotion criteria (`ml-models.md`); NFR assumptions (performance report) |
| 18 | Rollback owner named; procedure reviewed | ⏳ | `rollback-plan.md` |

## Scope of this release
See `Docs/stage-9/release-notes-v0.3.0.md`. Automated sensor ingestion (WP2)
was **descoped**, and readings are entered manually.
