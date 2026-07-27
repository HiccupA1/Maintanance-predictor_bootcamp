"""API v1 routers package."""
````I need to fix routing prefixes: `/health` must be unversioned and work-orders under `/v1`. Let me correct the aggregator.

Explanation: Correct prefixing so health is unversioned and work-order routes are under /v1.
````write file="Maintanance-predictor_bootcamp/app/api/v1/api.py"
"""API router aggregation.

Combines the health router (unversioned ``/health``) and the work order router
(served under the ``/v1`` prefix) into a single router included by the app.
"""

from fastapi import APIRouter

from app.api.v1.routers import health, work_orders

# PUBLIC_INTERFACE
api_router = APIRouter()
"""Top-level router combining health and versioned work order routes."""

# Health endpoints are intentionally unversioned per the contract.
api_router.include_router(health.router)
# Work order endpoints are served under the /v1 prefix.
api_router.include_router(work_orders.router, prefix="/v1")
