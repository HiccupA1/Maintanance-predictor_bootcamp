"""FastAPI application entrypoint for Work Order Management.

Wires OpenAPI metadata, structured logging, correlation-id middleware, the
RFC7807 problem exception handlers, and the API routers. Every non-health
route is authenticated (Supabase JWT) and authorized by the role policy in
``app/core/rbac.py``.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, set_correlation_id

configure_logging()
settings = get_settings()

# OpenAPI tag metadata for documentation grouping.
openapi_tags = [
    {"name": "health", "description": "Liveness and readiness probes."},
    {
        "name": "identity",
        "description": "Current-user identity (Supabase JWT in prod; optional DEV shim).",
    },
    {
        "name": "admin",
        "description": "Admin-only user and role management endpoints.",
    },
    {
        "name": "equipment",
        "description": "Equipment, thresholds, readings, and alert APIs.",
    },
    {
        "name": "work-orders",
        "description": "Create, update, fetch, and list work orders.",
    },
    {
        "name": "risk",
        "description": "Failure-risk scores and the model registry (WP4).",
    },
]

# PUBLIC_INTERFACE
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for Case (Work Order) Management. Implements the API "
        "Contract v0.2 with an RFC7807-like error model. All endpoints "
        "except health probes require a Supabase access token (RS256/ES256 "
        "via JWKS) and are authorized by role; GET /v1/me returns the "
        "authenticated user and role derived from the database. A DEV-only "
        "identity shim for /v1/me is available when APP_ENV=dev."
    ),
    openapi_tags=openapi_tags,
)
"""The FastAPI application instance (module-level entrypoint)."""


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Attach a correlation id to every request and response.

    Reads an incoming ``X-Correlation-Id`` header if present, otherwise
    generates one, binds it to the logging context, and echoes it back on the
    response for end-to-end tracing.
    """
    incoming = request.headers.get("X-Correlation-Id")
    cid = set_correlation_id(incoming)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = cid
    return response


register_exception_handlers(app)
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(api_router, prefix="/v1")
