# High-Level Design

The system is a React/Vite frontend backed by a FastAPI service and PostgreSQL database.

```text
Browser
  -> React routes, feature pages, hooks, API client
  -> FastAPI routers
  -> domain services
  -> repositories
  -> SQLAlchemy models
  -> PostgreSQL
```

Alembic manages schema migrations. The API exposes `/health`, `/health/db`, `/v1/...`, `/docs`, and `/openapi.json`. Structured errors use an RFC7807-like envelope and requests carry correlation IDs. The current identity endpoint is a development-only shim.
