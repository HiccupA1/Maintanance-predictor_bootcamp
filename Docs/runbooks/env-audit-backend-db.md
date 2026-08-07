[CodeWiki](../../../kavia-docs/CodeWiki/index.md) / [Onboarding](../../../kavia-docs/CodeWiki/Onboarding/index.md)

# Env audit: backend DB configuration (no secrets)

## Dotenv files discovered under `Maintanance-predictor_bootcamp/`
- `Maintanance-predictor_bootcamp/.env`
- `Maintanance-predictor_bootcamp/.env.example`
- `Maintanance-predictor_bootcamp/frontend/.env`
- `Maintanance-predictor_bootcamp/frontend/.env.example`

(Locations only; values intentionally not printed.)

## Backend: DB-related environment variables (expected/used)
Source: `Maintanance-predictor_bootcamp/app/core/config.py`

- `DATABASE_URL`
  - Used by `Settings.database_url`
  - Consumed by SQLAlchemy engine creation in `app/db/session.py`
  - Default if unset: `postgresql+psycopg2://postgres:postgres@localhost:5432/workorders`
  - Backend loads dotenv from: `Maintanance-predictor_bootcamp/.env`

## Related (Supabase/auth; not strictly DB, but relevant for hosted deployments)
Also defined in backend settings:
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `SUPABASE_JWKS_URL`
- `SUPABASE_JWT_AUDIENCE`
- `ENABLE_DEV_IDENTITY_SHIM`
