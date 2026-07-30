# Low-Level Design — Key Modules

## Backend

- `app/main.py`: application entrypoint, metadata, middleware, handlers, and router inclusion.
- `app/api/v1/routers`: HTTP transport and request validation.
- `app/services`: business rules and transaction boundaries.
- `app/repositories`: persistence queries and writes.
- `app/models`: SQLAlchemy entities and relationships.
- `app/schemas`: request/response contracts.
- `app/core`: settings, errors, and logging.

## Frontend

- `src/routes`: route composition.
- `src/features`: equipment, readings, alerts, and work-order screens.
- `src/api`: typed API calls.
- `src/hooks`: server-state access.
- `src/components`: shared controls and role gates.
- `src/utils/rbac.ts`: client-side action gating, never a replacement for backend enforcement.
