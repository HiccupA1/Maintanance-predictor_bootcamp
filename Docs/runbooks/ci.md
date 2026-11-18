# Continuous Integration

Workflow: `.github/workflows/ci.yml`. It runs on every pull request, on pushes to `main`, and
on manual dispatch.

## Jobs

| Job | What it checks | Blocking |
|---|---|---|
| Backend lint | `ruff check`, `black --check` on `app/` and `tests/` | Yes |
| Backend tests (py3.10, py3.12) | `pytest` on SQLite with coverage. JUnit and coverage XML are uploaded as artifacts | Yes |
| Frontend | `npm ci`, ESLint, `tsc --noEmit`, Vitest (JUnit artifact), production build | Yes |
| Migrations (Postgres) | `alembic upgrade head` on an empty Postgres 16, then downgrade/upgrade round trip | **No**, until D5 is fixed |
| Dependency audit | `pip-audit` (any finding); `npm audit --omit=dev` (high+); `npm audit` on all deps (critical). Accepted findings: `Docs/security/risk-register.md` | Yes |
| CI OK | Aggregates the blocking jobs into one status | This is the required check |

The non-blocking job still runs and shows its result on every pull request. It becomes
blocking in the pull request that fixes its defect: remove `continue-on-error` and add the job
to `ci-ok.needs`.

## Quarantined tests

Pre-existing failures are quarantined, not deleted. See the policy in
`Docs/stage-5/defect-log.md`.

- Backend: `tests/known_failures.py`, applied as strict xfails by `tests/conftest.py`.
- Frontend: `it.fails(...)` with a `// Quarantined: Dn` comment.

## Branch protection (repository admin, one-time)

In GitHub, go to **Settings → Branches → Add branch ruleset** (or classic rule) for `main`:

1. **Require a pull request before merging.** Required approvals: 1 (or 0 while the team is a
   single developer). Dismiss stale approvals when new commits are pushed.
2. **Require status checks to pass.** Add **`CI OK`**. It appears in the search box after the
   workflow has run at least once. Enable "Require branches to be up to date before merging".
3. **Block force pushes** and **restrict deletions**.
4. Optional: require linear history (squash or rebase merges).

## Running the same checks locally

```bash
# Backend (from repo root)
pip install -e ".[dev]"
ruff check app tests && black --check app tests
pytest -o addopts="" -ra --cov
pip-audit --skip-editable

# Frontend
cd frontend
npm ci
npm run lint && npm run typecheck && npm test && npm run build
npm audit --omit=dev --audit-level=high && npm audit --audit-level=critical
```
