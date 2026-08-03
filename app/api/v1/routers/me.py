"""Current-user identity routes.

In production, `/me` returns the authenticated user derived from a validated
Supabase JWT and the persisted `user_profiles` table.

In development, an optional header-driven identity shim may be enabled for UI
workflows that don't require Supabase (see `ENABLE_DEV_IDENTITY_SHIM`).
"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.errors import ErrorCode, ProblemException
from app.db.session import get_db
from app.models.user_profile import UserProfile
from app.schemas.domain import MeResponse

router = APIRouter(tags=["identity"])


# PUBLIC_INTERFACE
@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the current authenticated user",
    description=(
        "Returns the current authenticated user derived from a Supabase JWT and "
        "the persisted user profile. In DEV only, a header-driven identity shim "
        "can be enabled to support local RBAC testing without Supabase."
    ),
)
def get_current_user(
    db: Session = Depends(get_db),  # noqa: B008
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    user: UserProfile | None = Depends(get_current_user),
) -> MeResponse:
    """Return the current authenticated user.

    When Supabase auth is configured, this endpoint requires a valid bearer
    token. When `ENABLE_DEV_IDENTITY_SHIM=true`, it may fall back to the legacy
    header-driven identity (DEV-only).
    """
    # If we already resolved a JWT-authenticated user, return it.
    if user is not None:
        return MeResponse(
            user_id=user.supabase_user_id,
            name=user.display_name or user.email or "User",
            role=user.role,
        )

    # Otherwise, optionally allow the dev identity shim fallback.
    if not get_settings().enable_dev_identity_shim:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Authentication is required.",
        )

    allowed_roles = {"Admin", "PlantManager", "Operator", "MaintenanceEngineer"}
    role = x_user_role if x_user_role in allowed_roles else "PlantManager"
    return MeResponse(user_id="dev", name=x_user_name or "Dev User", role=role)
