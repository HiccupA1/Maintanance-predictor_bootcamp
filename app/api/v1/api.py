"""Version 1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1.routers import domain, me
from app.api.v1.routers import work_orders

# PUBLIC_INTERFACE
api_router = APIRouter()
"""Top-level v1 router combining all v1 sub-routers."""

# Work order endpoints are served under the /v1 prefix (added in main).
api_router.include_router(work_orders.router)
api_router.include_router(me.router)
api_router.include_router(domain.router)
