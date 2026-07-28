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
- The backend running and reachable (default `http://localhost:8000`)

## Install and run

```bash
cd frontend
npm install
npm run dev          # dev server on http://localhost:3000
npm run build        # type-check + production build
npm run preview      # serve the production build
```

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

## Running tests

```bash
cd frontend
npm test             # Vitest in non-interactive CI mode
npm run test:watch   # watch mode
npm run typecheck    # TypeScript only
```

Tests use Vitest + React Testing Library with a jsdom environment and mock the
`src/api/*` modules, so no backend is required.

## Routes

| Route | Screen |
| --- | --- |
| `/work-orders` | Work Orders list (pagination + status/priority filters) |
| `/work-orders/:id` | Work Order detail (incl. spare parts) |
| `/work-orders/:id/edit` | Edit Work Order |
| `/alerts/:alertId/convert` | Convert Alert → Work Order |

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
