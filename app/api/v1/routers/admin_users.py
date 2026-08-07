"""Admin user and role management endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.routers.me import get_current_user
from app.core.errors import ErrorCode, ProblemException, problem_responses
from app.db.session import get_db
from app.models.user_profile import UserProfile
from app.schemas.serialization import (
    coerce_uuid_to_str,
    normalize_datetime_to_utc,
)

router = APIRouter(tags=["admin"])


class UserProfileSummary(BaseModel):
    """Summary view of a user profile for admin listing."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Internal user profile id.")
    supabase_user_id: str = Field(..., description="Supabase Auth user id (sub).")
    email: str | None = Field(None, description="User email from Supabase.")
    display_name: str | None = Field(None, description="User display name.")
    role: str = Field(..., description="Persisted application role.")
    created_at: datetime | None = Field(
        default=None,
        description=(
            "Profile creation timestamp (UTC). Optional in responses to keep "
            "backward compatibility with earlier clients/tests."
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "Profile last-updated timestamp (UTC). Optional in responses to keep "
            "backward compatibility with earlier clients/tests."
        ),
    )

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id_to_str(cls, v: object) -> str:
        """Coerce UUID-like identifiers into string form."""
        return coerce_uuid_to_str(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamps_to_utc(cls, v: object) -> datetime | None:
        """Normalize tz-naive datetimes to UTC-aware values (preserve None)."""
        if v is None:
            return None
        return normalize_datetime_to_utc(v)


class ListUsersResponse(BaseModel):
    """Envelope for admin user listing."""

    items: list[UserProfileSummary] = Field(..., description="User profiles.")
    total: int = Field(..., description="Total number of profiles returned.")


class UpdateUserRoleRequest(BaseModel):
    """Payload for updating only a user's application role."""

    role: str = Field(
        ...,
        description=(
            "New role. Must be one of Admin, PlantManager, Operator, "
            "MaintenanceEngineer."
        ),
        min_length=1,
    )


class CreateUserRequest(BaseModel):
    """Payload for creating an application user profile."""

    supabase_user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase Auth user id.",
    )
    email: str | None = Field(None, description="User email address.")
    display_name: str | None = Field(None, description="User display name.")
    role: str = Field("Operator", description="Application role.")


class UpdateUserRequest(BaseModel):
    """Payload for updating profile metadata and role."""

    email: str | None = Field(None, description="User email address.")
    display_name: str | None = Field(None, description="User display name.")
    role: str = Field(..., description="Application role.")


_ALLOWED_ROLES = {
    "Admin",
    "PlantManager",
    "Operator",
    "MaintenanceEngineer",
}


def _validate_role(role: str) -> str:
    """Normalize and validate an application role."""
    normalized = role.strip()
    if normalized not in _ALLOWED_ROLES:
        raise ProblemException(
            status=422,
            code=ErrorCode.INVALID_REQUEST,
            detail=(
                "role must be one of Admin, PlantManager, Operator, "
                "MaintenanceEngineer."
            ),
        )
    return normalized


def _require_admin(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Enforce that the authenticated user has the Admin role."""
    if user.role != "Admin":
        raise ProblemException(
            status=403,
            code=ErrorCode.FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return user


def _get_profile_or_raise(
    supabase_user_id: str,
    db: Session,
) -> UserProfile:
    """Fetch a profile or raise the standard not-found problem."""
    row = db.execute(
        select(UserProfile).where(
            UserProfile.supabase_user_id == supabase_user_id
        )
    ).scalar_one_or_none()
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.INVALID_REQUEST,
            detail="User profile not found for the given supabase_user_id.",
            title="User Not Found",
        )
    return row


# PUBLIC_INTERFACE
@router.get(
    "/admin/users",
    response_model=ListUsersResponse,
    summary="List user profiles",
    description=(
        "Admin-only. Lists application user profiles with their persisted roles."
    ),
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
        items=[UserProfileSummary.model_validate(row) for row in rows],
        total=len(rows),
    )


# PUBLIC_INTERFACE
@router.post(
    "/admin/users",
    response_model=UserProfileSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user profile",
    description=(
        "Admin-only. Creates an application profile for an existing Auth user."
    ),
    responses=problem_responses(401, 403, 409, 422),
    dependencies=[Depends(_require_admin)],
)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> UserProfileSummary:
    """Create an application user profile."""
    role = _validate_role(payload.role)
    existing = db.execute(
        select(UserProfile).where(
            UserProfile.supabase_user_id == payload.supabase_user_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_REQUEST,
            detail="A profile already exists for the given supabase_user_id.",
        )

    row = UserProfile(
        supabase_user_id=payload.supabase_user_id,
        email=payload.email,
        display_name=payload.display_name,
        role=role,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return UserProfileSummary.model_validate(row)


# PUBLIC_INTERFACE
@router.put(
    "/admin/users/{supabase_user_id}",
    response_model=UserProfileSummary,
    summary="Update a user profile",
    description="Admin-only. Updates profile metadata and application role.",
    responses=problem_responses(401, 403, 404, 422),
    dependencies=[Depends(_require_admin)],
)
def update_user(
    payload: UpdateUserRequest,
    supabase_user_id: str = Path(..., description="Supabase Auth user id."),
    db: Session = Depends(get_db),  # noqa: B008
) -> UserProfileSummary:
    """Update an application user profile."""
    row = _get_profile_or_raise(supabase_user_id, db)
    row.email = payload.email
    row.display_name = payload.display_name
    row.role = _validate_role(payload.role)
    db.commit()
    db.refresh(row)
    return UserProfileSummary.model_validate(row)


# PUBLIC_INTERFACE
@router.delete(
    "/admin/users/{supabase_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user profile",
    description="Admin-only. Deletes an application user profile.",
    responses=problem_responses(401, 403, 404),
    dependencies=[Depends(_require_admin)],
)
def delete_user(
    supabase_user_id: str = Path(..., description="Supabase Auth user id."),
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete an application user profile."""
    row = _get_profile_or_raise(supabase_user_id, db)
    db.delete(row)
    db.commit()


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
    row = _get_profile_or_raise(supabase_user_id, db)
    row.role = _validate_role(payload.role)
    db.commit()
    db.refresh(row)
    return UserProfileSummary.model_validate(row)
