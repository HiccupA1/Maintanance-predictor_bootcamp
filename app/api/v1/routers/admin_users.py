"""Admin user and role management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.errors import ErrorCode, ProblemException, problem_responses
from app.db.session import get_db
from app.models.user_profile import UserProfile

router = APIRouter(tags=["admin"])


class UserProfileSummary(BaseModel):
    """Summary view of a user profile for admin listing."""

    id: str = Field(..., description="Internal user profile id.")
    supabase_user_id: str = Field(..., description="Supabase Auth user id (sub).")
    email: str | None = Field(None, description="User email from Supabase.")
    display_name: str | None = Field(None, description="User display name.")
    role: str = Field(..., description="Persisted application role.")


class ListUsersResponse(BaseModel):
    """Envelope for admin user listing."""

    items: list[UserProfileSummary] = Field(..., description="User profiles.")
    total: int = Field(..., description="Total number of profiles returned.")


class UpdateUserRoleRequest(BaseModel):
    """Payload for updating a user's application role."""

    role: str = Field(
        ...,
        description="New role. Must be one of Admin, PlantManager, Operator, MaintenanceEngineer.",
        min_length=1,
    )


_ALLOWED_ROLES = {"Admin", "PlantManager", "Operator", "MaintenanceEngineer"}

def _require_admin(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Enforce that the authenticated user has the Admin role."""
    if user.role != "Admin":
        raise ProblemException(
            status=403,
            code=ErrorCode.FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return user


# PUBLIC_INTERFACE
@router.get(
    "/admin/users",
    response_model=ListUsersResponse,
    summary="List user profiles",
    description="Admin-only. Lists application user profiles with their persisted roles.",
    responses=problem_responses(401, 403),
    dependencies=[Depends(_require_admin)],
)
def list_users(
    db: Session = Depends(get_db),  # noqa: B008
) -> ListUsersResponse:
    """List all user profiles ordered by email."""
    rows = (
        db.execute(select(UserProfile).order_by(UserProfile.email.asc()))
        .scalars()
        .all()
    )
    return ListUsersResponse(
        items=[
            UserProfileSummary(
                id=r.id,
                supabase_user_id=r.supabase_user_id,
                email=r.email,
                display_name=r.display_name,
                role=r.role,
            )
            for r in rows
        ],
        total=len(rows),
    )


# PUBLIC_INTERFACE
@router.put(
    "/admin/users/{supabase_user_id}/role",
    response_model=UserProfileSummary,
    summary="Update a user's role",
    description="Admin-only. Updates the persisted application role for a user.",
    responses=problem_responses(401, 403, 404, 422),
    dependencies=[Depends(_require_admin)],
)
def update_user_role(
    payload: UpdateUserRoleRequest,
    supabase_user_id: str = Path(..., description="Supabase Auth user id (sub)."),
    db: Session = Depends(get_db),  # noqa: B008
) -> UserProfileSummary:
    """Update the persisted role for a user profile."""
    role = payload.role.strip()
    if role not in _ALLOWED_ROLES:
        raise ProblemException(
            status=422,
            code=ErrorCode.INVALID_REQUEST,
            detail="role must be one of Admin, PlantManager, Operator, MaintenanceEngineer.",
        )

    row = db.execute(
        select(UserProfile).where(UserProfile.supabase_user_id == supabase_user_id)
    ).scalar_one_or_none()
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.INVALID_REQUEST,
            detail="User profile not found for the given supabase_user_id.",
            title="User Not Found",
        )

    row.role = role
    db.commit()
    db.refresh(row)

    return UserProfileSummary(
        id=row.id,
        supabase_user_id=row.supabase_user_id,
        email=row.email,
        display_name=row.display_name,
        role=row.role,
    )
