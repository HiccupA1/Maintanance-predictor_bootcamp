# Vercel deployment (frontend preview)

This repository contains a Python backend (`Maintanance-predictor_bootcamp/`) and a Vite frontend (`Maintanance-predictor_bootcamp/frontend/`).

A minimal Vercel configuration is provided at:

- `Maintanance-predictor_bootcamp/vercel.json`

It instructs Vercel to build and serve the **frontend** as a static single-page app (SPA) preview.

## Vercel project settings

When creating the Vercel project, set:

- **Root Directory**: `Maintanance-predictor_bootcamp`
- **Framework Preset**: Vite (auto-detected by `framework: "vite"` in `vercel.json`)
- **Build Command**: (already set in `vercel.json`) `cd frontend && npm run build`
- **Output Directory**: (already set in `vercel.json`) `frontend/dist`
- **Install Command**: (already set in `vercel.json`) `cd frontend && npm ci --no-audit --no-fund`

## SPA routing

The `rewrites` rule in `vercel.json` routes all paths to `/` so client-side routes like:

- `/work-orders`
- `/equipment/:id`
- `/alerts/:alertId`

work correctly on refresh.

## Required environment variables

The frontend reads runtime configuration via Vite build-time environment variables:

- `VITE_API_BASE_URL` (example: `https://<your-backend-host>`)

If `VITE_API_BASE_URL` is not set, the frontend falls back to `http://localhost:8000`, which will not work in a Vercel-hosted preview unless the backend is also reachable there.

> Note: Vite only exposes variables prefixed with `VITE_`, and values are inlined at build time.

## Preview-only scope

This config deploys only the frontend preview. It does not deploy the backend from this repository.
