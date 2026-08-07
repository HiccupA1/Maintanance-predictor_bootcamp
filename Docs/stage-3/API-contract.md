# API Contract

The authoritative generated schema is available at [`/openapi.json`](/openapi.json), with interactive Swagger UI at [`/docs`](/docs).

## Contract conventions

- Versioned business routes use `/v1`.
- Errors use `application/problem+json`.
- Error fields include `type`, `title`, `status`, `detail`, `instance`, `code`, `correlation_id`, and `errors`.
- Work-order priorities are `CRITICAL`, `HIGH`, or `MEDIUM`.
- Work-order statuses are `OPEN` or `CLOSED`.
- List endpoints support validated pagination and filters.

## Primary routes

| Method | Path |
|---|---|
| GET | `/v1/me` |
| GET/POST | `/v1/equipment` |
| GET/PUT | `/v1/equipment/{equipment_id}` |
| POST | `/v1/readings` |
| GET | `/v1/alerts` |
| POST | `/v1/work-orders` |
| GET | `/v1/work-orders/{work_order_id}` |
| PUT | `/v1/work-orders/{work_order_id}` |
| GET | `/v1/work-orders` |
| GET | `/v1/health` |
| GET | `/v1/health/db` |
