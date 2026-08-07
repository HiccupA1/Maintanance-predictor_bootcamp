# UI Preview Notes (Modern “World-Class” Theme)

This update is **visual-only**: no routes, API calls, auth, or business logic were changed.

## What changed
- **Aurora background** + **glassmorphism** surfaces across the app.
- **Premium header** (spotlight/gradient) with upgraded nav states.
- Unified **Card / Input / Table / Badge / Button** styling.
- Updated microcopy/placeholder text to feel more modern and product-grade.

## Where to look
- Header + navigation: `src/layouts/AppShell.tsx` (styling via `src/index.css`)
- Global design tokens & component primitives: `src/index.css`
- UI primitives:
  - `src/components/ui/Button.tsx`
  - `src/components/ui/Badge.tsx`
  - `src/components/ui/EmptyState.tsx`
  - `src/components/ui/ErrorPanel.tsx`

## Preview (how to generate locally)
### Install & run (dev preview)
From the repo root:

```bash
cd Maintanance-predictor_bootcamp/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run dev:safe:preview
```

Notes:
- `--ignore-scripts` is a workaround for this environment where `npm ci` can fail during native binary install steps.
- `dev:safe:preview` binds to `0.0.0.0:3000` and disables Vite plugins for stability.

Optional (dev-only): bypass auth redirects for UI testing:
```bash
VITE_BYPASS_AUTH=1 npm run dev:safe:preview
```

### Production build (smoke check)
```bash
npm run build
```

### What to capture
Take a screenshot of:
- `/readings`
- `/work-orders`
- `/alerts`

This repository is configured with Vite/Tailwind; any standard screenshot method (browser capture) will work.

If you need a static build preview:
```bash
npm run preview
```
