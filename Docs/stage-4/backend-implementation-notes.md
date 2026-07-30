# Backend Implementation Notes

The backend uses FastAPI, SQLAlchemy 2.x, PostgreSQL, and Alembic. Requests enter versioned routers, pass through domain services, and use repositories for persistence. Work-order creation atomically inserts the work order and transitions the source alert. Closure updates the work order, equipment service date, and alert state.

Configuration is loaded from environment variables. Run migrations with `alembic upgrade head`, start with `uvicorn app.main:app --host 0.0.0.0 --port 8000`, and inspect `/docs` or `/openapi.json`.
