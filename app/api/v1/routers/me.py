"""Development identity and RBAC shim routes."""

from fastapi import APIRouter, Header

from app.schemas.domain import MeResponse

router = APIRouter(tags=["identity"])


# PUBLIC_INTERFACE
@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the development identity",
    description=(
        "Development-only identity shim. Authentication is not enforced. "
        "Use X-User-Role and optional X-User-Name headers for frontend RBAC tests."
    ),
)
def get_current_user(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
) -> MeResponse:
    """Return a non-secure identity derived from development request headers."""
    allowed_roles = {"Admin", "PlantManager", "Operator", "MaintenanceEngineer"}
    role = x_user_role if x_user_role in allowed_roles else "PlantManager"
    return MeResponse(user_id="dev", name=x_user_name or "Dev User", role=role)
