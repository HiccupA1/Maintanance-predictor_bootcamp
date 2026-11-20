# Release Notes: v0.3.0

**Scope:** CR-001 (ML-assisted failure risk), without WP2. Readings stay
manual entry, because automated sensor ingestion was descoped on 2026-11-19.

## New
- **Failure-risk scoring (WP3, WP4).** A reproducible training pipeline on
  AI4I 2020, with a model card.
  - A model registry with SHA-256-verified artifacts.
  - Every reading on a configured machine is scored after the response.
  - Per-machine risk panel. Model-raised alerts are badged.
- **Shadow-first rollout.** New models score silently and are visible to
  Admins only. Activating one is an audited Admin action that verifies the
  artifact first.
- **Model operations (WP5).**
  - Shadow evaluation against confirmed failures, side by side with
    threshold alerts.
  - PSI drift monitoring, plus a scheduled monitor that exits non-zero on
    significant drift.
  - Retraining on the client's own failure labels, with a champion/challenger
    gate.
  - Admin → Models page.
- **Work-order closure (FR7, FR9, FR10).**
  - A work order is linked to its source alert, one per alert.
  - Closing requires resolution notes, a root cause and the failure label
    (confirmed? which mode?).
  - Closing resolves the alert and updates the equipment's service date.

## Security
- Authentication and role checks on **every** route, from one central
  policy. Completeness is tested (D7).
- The dev identity shim is off by default and refused outside `APP_ENV=dev`
  (D14).
- **Direct Supabase Data API access is closed** (D17).
- The post-login open redirect is fixed; dependency vulnerabilities are
  cleared or risk-accepted (D12, D13).
- Personal data is removed from code, docs and the login page (D16).
- WP6 hardening: https-only JWKS, generic auth errors, docs off in
  production, security headers, input limits.

## Platform
- A single **Alembic baseline** is the schema source of truth (D5). The
  Supabase SQL is archived.
- **Container image:** non-root, health check, the same image runs
  migrations. Plus a `docker-compose.yml` for local development.
- **CI**, all on one required **CI OK** check:
  - lint, tests, migrations (plain and Supabase-stub paths);
  - frontend;
  - dependency audit (bandit, pip-audit, npm);
  - image build, smoke test and Trivy scan.
  - The ML golden retrain and the load test run as non-blocking evidence jobs.
- **Performance:** at 3× the baseline load, p95 is 102 ms with no errors
  (`performance-report.md`).

## Fixed
- D4 (a 500 on `page_size=200`).
- D6 (health path).
- D8, partly: a UUID column type on SQLite.

## Breaking changes and operator notes
- **Python 3.12** is required.
- **Database:**
  - apply the baseline stamp, then migrations 0002 to 0004;
  - the API's database role must bypass RLS;
  - see `Docs/runbooks/database-migrations.md`.
- **New settings:**
  - `APP_ENV` (default `production`);
  - `MODEL_STORE_DIR`, `SCORING_ENABLED`;
  - `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_S`;
  - `API_DOCS_ENABLED`.
- Health probes are at **`/v1/health`** and **`/v1/health/db`**.
- The first Admin is created with `scripts/seed_admin.py`. No email is
  hard-coded.

## Known limitations
- The AI4I model is trained on **synthetic** data, so its metrics do not
  predict field accuracy. Real performance is established in shadow mode
  against confirmed failures.
- Not yet built: the label-free anomaly model (ADR-0006), the Supabase
  Storage model store, a persisted monitoring history, an audit-log table,
  spare-parts lines, and pagination on `/alerts` and readings history.
- Readiness gates still open: `Docs/stage-8/release-readiness-checklist.md`.
