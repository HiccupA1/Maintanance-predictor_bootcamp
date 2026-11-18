# Security Risk Register: Accepted Dependency Findings

Each accepted finding records what is accepted, why, what limits its exposure, and when it is
re-reviewed. CI (`.github/workflows/ci.yml`, job `security`) enforces these gates:

- Python: `pip-audit` blocks on **any** known vulnerability. To accept one, pass an explicit
  `--ignore-vuln <ID>` in CI that references an entry here.
- npm, production dependencies (`--omit=dev`): blocks on **high** and above.
- npm, all dependencies, including build and test tooling: blocks on **critical**.

Dependabot (`.github/dependabot.yml`) raises an upgrade PR as soon as a fixed version is
published.

| ID | Package / advisory | Severity | Scope | Status | Review by |
|---|---|---|---|---|---|
| RA-1 | `picomatch` ≤ 4.0.7: ReDoS via single-branch repeated extglobs. Reached through `vite`, `vitest`, `tinyglobby`/`fdir`, `typescript-eslint`, and `tailwindcss` 3 (`chokidar`, `fast-glob`, `micromatch`, `anymatch`, `readdirp`). | High (17 npm entries) | Dev and build tooling only. Not in the browser bundle. | Accepted 2026-11-18 | 2027-02-18, or when a patched `picomatch` is released |
| RA-2 | `react-router` 6.x: (a) open redirect via backslash in `<Link>` / `useNavigate`; (b) constructor injection in SSR hydration `deserializeErrors()`. Fixed only in 7.18+. | Moderate (2) | Production bundle | Accepted with mitigation 2026-11-18. The v7 migration is tracked as D15. | 2027-01-31 |

## RA-1 rationale

- **No fixed version exists.** The latest `picomatch` (4.0.7) is inside the advisory range.
  npm's suggested "fixes" are downgrades (for example Vite 6.2.7) that drop the dependency
  edge rather than fix it, and they would reintroduce the patched Vite and Vitest criticals.
- **Exposure:** glob patterns come from repository configuration (Tailwind `content`, Vite and
  Vitest include rules, ESLint). No user-controlled input reaches `picomatch` at build or test
  time, and none of these packages run in production.
- **Residual risk:** a malicious pattern committed to the repository could slow a build. This
  is covered by code review on protected `main`.

## RA-2 rationale

- **(a) Open redirect.** The only navigation to a user-controlled target is the post-login
  `?next=` / `state.from` redirect in `LoginPage`. Since 2026-11-18 it is validated by
  `safeNextPath` (`frontend/src/utils/safeRedirect.ts`), which rejects backslashes, control
  characters, protocol-relative and absolute URLs, and anything that resolves cross-origin.
  It has unit tests in `safeRedirect.test.ts`. Any new navigation to an external or
  user-supplied target must go through the same helper.
- **(b) SSR hydration.** Not applicable. The frontend is a client-rendered SPA (Vite, no SSR or
  React Router framework mode), so `deserializeErrors()` hydration data is never produced or
  consumed.
- **Exit:** migrate to React Router 7 (D15). v7 keeps the library-mode API used here, so the
  migration is mostly import and future-flag changes.
