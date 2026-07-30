# Maintenance Work Orders — Frontend

React + Vite + TypeScript + Tailwind CSS frontend for the **Work Orders journey**
of the Predictive Maintenance Alert & Work Order System.

Screens and wording follow the Stage 2 UX design doc
(`kavia-docs/CodeWiki/Specs/DetailedDesigns/stage-2-ux-flows-and-ui.md`), and the
API integration follows the Stage 4/5B backend contract implemented in
`Maintanance-predictor_bootcamp/`.

## Why `frontend/`

The repository already contains the Python backend at
`Maintanance-predictor_bootcamp/`. A sibling `frontend/` folder keeps the two
deployables clearly separated at the repository root without introducing an
extra `apps/` monorepo layer that nothing else needs yet.

## Prerequisites

- Node.js 18+ and npm 9+
- Vite 6.1.0 is pinned for compatibility with the native esbuild runtime on the
  supported Linux/Node 18 environment.
- The backend running and reachable (default `http://localhost:8000`)

## Install and run

```bash
cd frontend
npm ci
npm run dev          # dev server on http://localhost:3000
npm run build        # type-check + production build
npm run preview      # serve the production build
```

If `package.json` is changed, regenerate and commit `package-lock.json` with
`npm install` before using `npm ci`.

### Constrained install environments

This frontend includes `bin-links=false` because some supported environments do
not permit npm to create symlinks. The native esbuild install script must remain
enabled because Vite requires the platform-specific esbuild executable at build
and test time. Run `npm ci` or `npm install` normally; do not pass
`--ignore-scripts`.

## Configuring `VITE_API_BASE_URL`

The API base URL is environment-driven and never hard-coded.

1. Copy the example file and adjust the value:

   ```bash
   cp .env.example .env
   ```

2. Set the backend origin (no trailing slash, no `/v1` suffix):

   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```

If the variable is unset, the app falls back to `http://localhost:8000`.
Vite only exposes variables prefixed with `VITE_`, and the value is inlined at
build time — rebuild after changing it.

> For non-local environments, request the correct value from the user/orchestrator
> so it can be written into `.env`.

## Development persona switcher

When running through Vite development mode, the header includes a **Dev persona**
button group for switching among **Admin**, **Plant Manager**, **Operator**, and
**Maintenance Engineer**. The selected identity is saved in browser local
storage, and the current page reloads so all API calls send the updated
`X-User-Role` and `X-User-Name` headers to the backend development identity
shim.

The switcher is omitted from production builds. Its initial role uses
`VITE_USER_ROLE` when valid (otherwise the backend-compatible `PlantManager`
default), and its initial display name uses `VITE_USER_NAME`.

## Running tests

```bash
cd frontend
npm test             # Vitest in non-interactive CI mode
npm run test:watch   # watch mode
npm run typecheck    # TypeScript only
```

Tests use Vitest + React Testing Library with a jsdom environment and mock the
`src/api/*` modules, so no backend is required.

## Routes and persona access

All four personas can open the list and detail routes below. Current
role-specific controls are shown within the applicable pages; the documented
action permissions reflect the frontend's current RBAC implementation.

| Route | Screen | Intended persona access |
| --- | --- | --- |
| `/` | Default entry | Redirects to `/work-orders` for all personas. |
| `/work-orders` | Work Orders list | All personas. |
| `/work-orders/:id` | Work Order detail | All personas; only **Maintenance Engineers** see the close-work-order controls. |
| `/work-orders/:id/edit` | Edit Work Order | All personas currently have the edit route available; closed records remain read-only. |
| `/equipment` | Equipment list | All personas; only **Admins** see **Add equipment**. |
| `/equipment/new` | Add equipment | **Admin** only. |
| `/equipment/:id` | Equipment detail and parameters | All personas; **Admins** can edit equipment and **Plant Managers** can add or edit parameters. |
| `/equipment/:id/edit` | Edit equipment | **Admin** only. |
| `/readings` | Manual reading capture and history | All personas can review the page/history; only **Operators** can capture or correct readings. |
| `/alerts` | Alerts list | All personas. |
| `/alerts/:alertId` | Alert detail | All personas; only **Plant Managers** see **Convert to Work Order**. |
| `/alerts/:alertId/convert` | Convert alert to work order | **Plant Manager** only. |
| `*` | Not found | All personas; shown for unknown paths. |

`/` redirects to `/work-orders`.

## Backend endpoints used

| Method | Path |
| --- | --- |
| GET | `/v1/work-orders` |
| GET | `/v1/work-orders/{work_order_id}` |
| PUT | `/v1/work-orders/{work_order_id}` |
| POST | `/v1/alerts/{alert_id}/work-orders` |
| GET | `/health` (shell health indicator) |
| GET | `/health/db` (shell health indicator) |

## Project structure

```
frontend/
├── src/
│   ├── api/           # client.ts (fetch wrapper + Problem JSON normalization),
│   │                  # workOrders.ts, health.ts — all network access
│   ├── components/ui/ # Button, Badge, EmptyState, ErrorPanel, Spinner
│   ├── config/env.ts  # VITE_API_BASE_URL, /v1 prefix, page-size limits
│   ├── features/      # workOrders/* and alerts/* screens
│   ├── hooks/         # useWorkOrders.ts, useBackendHealth.ts — page logic
│   ├── layouts/       # AppShell (header + nav + health indicator)
│   ├── routes/        # AppRoutes
│   ├── test/          # Vitest setup + shared render helpers and fixtures
│   ├── types/         # Backend contract types
│   └── utils/         # Date formatting helpers
```

## UI state handling

Every API call renders four explicit states:

- **Loading** — skeletons on list/detail, busy buttons on submit
- **Error** — `ErrorPanel` shows the Problem JSON `detail`/`title`, `code`,
  field errors and `correlation_id`; never a stack trace
- **Empty** — "No work orders found" on the list, "Work order not found" on detail
- **Success** — rendered data

Pagination supports `page` and `page_size` (clamped client-side to ≤ 200) and
shows the total count plus the current page. Conflict cases are handled
explicitly: closed work orders cannot be edited, and a duplicate conversion
attempt explains that only one work order is permitted per alert.
