"""Authentication and authorization helpers.

This module validates Supabase JWT access tokens and provides FastAPI
dependencies for:

- extracting the authenticated principal
- mapping/upserting a UserProfile row
- enforcing role-based access control (RBAC)

JWT verification approach:
- Uses Supabase JWKS (asymmetric verification) via `/.well-known/jwks.json`.
- This avoids relying on legacy symmetric secrets (`SUPABASE_JWT_SECRET`).

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


def _supabase_jwks_url() -> str:
    """Return the Supabase JWKS URL derived from settings."""
    settings = get_settings()
    if settings.supabase_jwks_url and settings.supabase_jwks_url.strip():
        return settings.supabase_jwks_url.strip()
    if settings.supabase_url and settings.supabase_url.strip():
        base = settings.supabase_url.strip().rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json"
    return ""


def _jwt_verify_rs256_supabase(token: str) -> dict[str, Any]:
    """Verify a Supabase-issued RS256 JWT using the project's JWKS.

    This uses PyJWT's JWKS client and validates signature + expiration.
    Audience validation is optional via `SUPABASE_JWT_AUDIENCE`.

    Raises:
        ProblemException: 401 if token is missing/invalid/expired.
    """
    import jwt
    from jwt import PyJWKClient

    settings = get_settings()
    jwks_url = _supabase_jwks_url()
    if not jwks_url:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=(
                "Supabase JWT verification is not configured on the API. "
                "Set SUPABASE_URL (or SUPABASE_JWKS_URL) so the backend can "
                "fetch /.well-known/jwks.json."
            ),
        )

    # Quick check to fail fast for non-RS256 tokens.
    header, _payload = _jwt_decode_header_payload(token)
    alg = header.get("alg")
    if alg != "RS256":
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=f"Unsupported JWT algorithm; expected RS256, got {alg!r}.",
        )

    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token).key
    except Exception:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Unable to fetch or resolve signing key from Supabase JWKS.",
        )

    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": bool(settings.supabase_jwt_audience.strip())
        if isinstance(settings.supabase_jwt_audience, str)
        else False,
    }

    try:
        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.supabase_jwt_audience.strip()
            if isinstance(settings.supabase_jwt_audience, str)
            and settings.supabase_jwt_audience.strip()
            else None,
            options=options,
        )
    except jwt.ExpiredSignatureError:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Token is expired.",
        )
    except jwt.InvalidTokenError:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="Invalid token.",
        )

    return decoded


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
    payload = _jwt_verify_rs256_supabase(token)
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


def get_optional_current_user(
    principal: SupabasePrincipal | None = Depends(get_principal),
    db: Session = Depends(get_db),  # noqa: B008
) -> UserProfile | None:
    """Return the authenticated profile, or ``None`` when no token is supplied.

    This dependency is intended only for endpoints that provide a separate
    development identity fallback. Protected endpoints must continue using
    :func:`get_current_user`.

    Args:
        principal: Validated Supabase principal, if a bearer token was supplied.
        db: Database session used for profile lookup or creation.

    Returns:
        The persisted profile for an authenticated principal, otherwise ``None``.
    """
    if principal is None:
        return None
    return get_current_user(principal=principal, db=db)


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
