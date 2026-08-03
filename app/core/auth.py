"""Authentication and authorization helpers.

This module validates Supabase JWT access tokens and provides FastAPI
dependencies for:

- extracting the authenticated principal
- mapping/upserting a UserProfile row
- enforcing role-based access control (RBAC)

JWT verification approach:
- Uses HS256 and `SUPABASE_JWT_SECRET` (configured in Supabase project settings).
- If you use RS256/JWKS instead, this module must be updated accordingly.

Security note:
- Application roles are derived exclusively from the database (user_profiles).
  We do not accept roles from JWT custom claims to avoid client-side forgery.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Iterable

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ErrorCode, ProblemException
from app.db.session import get_db
from app.models.user_profile import UserProfile


@dataclass(frozen=True)
class SupabasePrincipal:
    """Decoded identity information from a validated Supabase JWT."""

    supabase_user_id: str
    email: str | None
    display_name: str | None
    raw_claims: dict[str, Any]


def _b64url_decode(segment: str) -> bytes:
    """Decode a base64url JWT segment into bytes."""
    # Pad to multiple of 4.
    padding = "=" * ((4 - (len(segment) % 4)) % 4)
    import base64

    return base64.urlsafe_b64decode(segment + padding)


def _jwt_signing_input(token: str) -> bytes:
    """Return the signing input bytes for a JWT (header.payload)."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT must have 3 segments")
    return f"{parts[0]}.{parts[1]}".encode("utf-8")


def _jwt_decode_header_payload(token: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Decode JWT header and payload without validating signature."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT must have 3 segments")
    header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
    payload = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    return header, payload


def _jwt_verify_hs256(token: str, secret: str) -> dict[str, Any]:
    """Verify HS256 JWT signature and return payload.

    Raises:
        ProblemException: 401 if token is missing/invalid/expired.
    """
    import base64
    import hashlib
    import hmac

    header, payload = _jwt_decode_header_payload(token)
    if header.get("alg") != "HS256":
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Unsupported JWT algorithm; expected HS256.",
        )

    signing_input = _jwt_signing_input(token)
    signature = token.split(".")[2]
    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()
    expected_b64 = base64.urlsafe_b64encode(expected).decode("utf-8").rstrip("=")
    if not hmac.compare_digest(expected_b64, signature):
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Invalid token signature.",
        )

    # Basic expiry validation.
    now = int(time.time())
    exp = payload.get("exp")
    if isinstance(exp, int) and now >= exp:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Token is expired.",
        )

    return payload


# PUBLIC_INTERFACE
def get_principal(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> SupabasePrincipal | None:
    """Extract and validate the Supabase JWT from the Authorization header.

    Args:
        authorization: The standard `Authorization: Bearer <token>` header.

    Returns:
        SupabasePrincipal: Decoded and validated principal identity.

    Raises:
        ProblemException: 401 when the request is unauthenticated/invalid.
    """
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Authorization header must be a Bearer token.",
        )
    token = authorization.split(" ", 1)[1].strip()
    secret = get_settings().supabase_jwt_secret
    if not secret:
        return None

    payload = _jwt_verify_hs256(token, secret)
    supabase_user_id = payload.get("sub")
    if not isinstance(supabase_user_id, str) or not supabase_user_id:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Token does not contain a valid subject (sub).",
        )

    email = payload.get("email")
    if email is not None and not isinstance(email, str):
        email = None

    # Supabase often provides user_metadata in app_metadata/user_metadata.
    display_name: str | None = None
    user_metadata = payload.get("user_metadata")
    if isinstance(user_metadata, dict):
        name = user_metadata.get("name") or user_metadata.get("full_name")
        if isinstance(name, str) and name.strip():
            display_name = name.strip()

    return SupabasePrincipal(
        supabase_user_id=supabase_user_id,
        email=email,
        display_name=display_name,
        raw_claims=payload,
    )


# PUBLIC_INTERFACE
def get_current_user(
    principal: SupabasePrincipal | None = Depends(get_principal),
    db: Session = Depends(get_db),  # noqa: B008
) -> UserProfile:
    """Return the current application user, upserting a profile if needed.

    Creates the user profile on first-seen access with a default role
    (`Operator`) so an admin can later assign the final role.

    Args:
        principal: Validated Supabase principal extracted from JWT.
        db: Database session.

    Returns:
        UserProfile: Persisted user profile including role.
    """
    if principal is None:
        # Allows DEV-only /me shim fallback when configured.
        # Callers that require auth should use `require_roles(...)` or validate
        # principal presence themselves.
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Authentication is required.",
        )
    row = db.execute(
        select(UserProfile).where(
            UserProfile.supabase_user_id == principal.supabase_user_id
        )
    ).scalar_one_or_none()

    if row is None:
        row = UserProfile(
            supabase_user_id=principal.supabase_user_id,
            email=principal.email,
            display_name=principal.display_name,
            role="Operator",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    # Keep basic profile info up-to-date; role is only admin-managed.
    updated = False
    if principal.email and principal.email != row.email:
        row.email = principal.email
        updated = True
    if principal.display_name and principal.display_name != row.display_name:
        row.display_name = principal.display_name
        updated = True
    if updated:
        db.commit()
        db.refresh(row)
    return row


# PUBLIC_INTERFACE
def require_roles(
    allowed_roles: Iterable[str],
):
    """Build a dependency that enforces the current user has one of the roles.

    Args:
        allowed_roles: Roles allowed to access an endpoint.

    Returns:
        Callable: A FastAPI dependency function.
    """

    allowed = {r.strip() for r in allowed_roles if r and r.strip()}

    def _dependency(
        user: UserProfile = Depends(get_current_user),
    ) -> UserProfile:
        if user.role not in allowed:
            raise ProblemException(
                status=403,
                code=ErrorCode.FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return _dependency
