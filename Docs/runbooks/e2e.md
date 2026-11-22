# Browser E2E Tests (Playwright)

Specs live in `frontend/e2e/specs/`, and the full catalogue is in
`Docs/stage-7/e2e-test-matrix.md`.

## What runs
- **Frontend:** a production build of the frontend (`vite build`, then
  `vite preview`).
- **API:** the real FastAPI app (uvicorn), started by Playwright.
- **Database:** a disposable Postgres, migrated to head.

### Authentication
`tools/testenv` generates an RS256 key and writes the following for each
role:
- `jwks.json`;
- an access token;
- a **Supabase-shaped session**.

Each test then:
- puts the session into the browser's localStorage key
  `sb-localhost-auth-token`, which is where supabase-js reads it from;
- the API verifies the token through its real JWKS code
  (`SUPABASE_JWKS_URL=file://…`, allowed only with `APP_ENV=test`);
- only Supabase's own HTTP endpoints (`/auth/v1/token`, `/user`, `/logout`)
  are stubbed, so the sign-in form can also be tested.

### Data
Each test creates its own uniquely named records, so tests run in parallel
with no database reset.

## Run locally

```powershell
# 1. Postgres for tests (any disposable database)
$env:DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5432/e2e"
$env:MODEL_STORE_DIR = "$PWD\reports\e2e-env\models"
$env:APP_ENV = "test"
alembic upgrade head

# 2. Train the model the UI scores with (once), then seed
python -m ml.pipelines.train_ai4i --version ai4i-v1
python -m tools.testenv.seed reports\e2e-env

# 3. Run (from frontend/)
cd frontend
npm run e2e:install      # first time: downloads Chromium
$env:E2E_PYTHON = "..\.venv\Scripts\python.exe"
npm run e2e              # whole suite
npm run e2e -- readings  # one spec file
npm run e2e -- --ui      # interactive runner
```

- **Report:** `frontend/reports/e2e-html/index.html`. Failures keep a trace,
  video and screenshot (`npx playwright show-trace <zip>`).
- **Re-seeding:** reruns reuse the seeded database. If you re-seed, restart
  the API, which caches the JWKS for 5 minutes.

## Rules
- **No retries.** A test that needs one to pass counts as failing.
- **Quarantine:** a test that exposes a defect that can't be fixed in the same
  PR is marked `test.fixme()`, with a `// Quarantined: Dn` comment and a row in
  `Docs/stage-5/defect-log.md`. This is the same ratchet as the unit tests.
- **Selectors:** prefer roles, labels and visible text, which also keeps the UI
  accessible. Add a `data-testid` only where no accessible selector exists.
- **New pages:** add the page to `rbac.spec.ts` and `a11y.spec.ts`.

## Workflow benchmark
`workflow-benchmark.spec.ts` records every user action of the app flow to
`reports/workflow-app.json`. Then run:

```bash
python -m tools.workflow_benchmark.report
```

This regenerates `Docs/stage-9/workflow-comparison.md`.
