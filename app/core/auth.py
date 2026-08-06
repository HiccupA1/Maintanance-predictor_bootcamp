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
import logging
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

logger = logging.getLogger(__name__)


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


_JWKS_CACHE: dict[str, Any] = {"expires_at": 0.0, "jwks": None, "url": ""}


def _fetch_supabase_jwks(jwks_url: str) -> dict[str, Any]:
    """Fetch and parse the Supabase JWKS document.

    We intentionally keep this dependency-free (urllib) to avoid adding new
    runtime dependencies. Failures are surfaced with actionable diagnostics.
    """
    import ssl
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        jwks_url,
        headers={
            "Accept": "application/json",
            # Some CDNs behave better with a UA.
            "User-Agent": "work-order-management-api/1.0 (jwks-fetch)",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5, context=ssl.create_default_context()) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        # Keep message short; details are logged server-side.
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=f"Failed to fetch Supabase JWKS (HTTP {e.code}) from {jwks_url}.",
        ) from e
    except urllib.error.URLError as e:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=(
                "Failed to fetch Supabase JWKS due to a network/SSL error. "
                f"JWKS URL: {jwks_url}. Cause: {type(e).__name__}: {e}."
            ),
        ) from e
    except Exception as e:  # noqa: BLE001
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=(
                "Failed to fetch Supabase JWKS due to an unexpected error. "
                f"JWKS URL: {jwks_url}. Cause: {type(e).__name__}: {e}."
            ),
        ) from e

    try:
        jwks = json.loads(raw)
    except Exception as e:  # noqa: BLE001
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=f"Supabase JWKS response was not valid JSON. JWKS URL: {jwks_url}.",
        ) from e

    if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=f"Supabase JWKS response did not contain a 'keys' array. JWKS URL: {jwks_url}.",
        )
    return jwks


def _get_cached_jwks(jwks_url: str, ttl_seconds: int = 300) -> dict[str, Any]:
    """Return a cached JWKS document, refreshing it when expired."""
    now = time.time()
    cached = _JWKS_CACHE.get("jwks")
    if (
        cached is not None
        and _JWKS_CACHE.get("url") == jwks_url
        and float(_JWKS_CACHE.get("expires_at") or 0.0) > now
    ):
        return cached

    jwks = _fetch_supabase_jwks(jwks_url)
    _JWKS_CACHE["jwks"] = jwks
    _JWKS_CACHE["url"] = jwks_url
    _JWKS_CACHE["expires_at"] = now + ttl_seconds
    return jwks


def _select_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    """Select a JWK from a JWKS document by kid."""
    keys = jwks.get("keys") or []
    for key in keys:
        if isinstance(key, dict) and key.get("kid") == kid:
            return key
    return None


def _public_key_from_jwk(jwk: dict[str, Any], alg: str):
    """Convert a JWK dict to a PyJWT public key object for the given algorithm."""
    import jwt

    # PyJWT expects the JWK as JSON string for from_jwk.
    jwk_json = json.dumps(jwk)
    if alg == "RS256":
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
    if alg == "ES256":
        return jwt.algorithms.ECAlgorithm.from_jwk(jwk_json)
    raise ValueError(f"Unsupported alg {alg!r} for JWK conversion")


def _jwt_verify_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify a Supabase-issued JWT (RS256 or ES256) using the project's JWKS.

    This uses PyJWT's JWKS client and validates signature + expiration.
    Audience validation is optional via `SUPABASE_JWT_AUDIENCE`.

    Raises:
        ProblemException: 401 if token is missing/invalid/expired.
    """
    import jwt

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

    # Quick check to fail fast for unsupported algorithms, and to guide users.
    header, _payload = _jwt_decode_header_payload(token)
    alg = header.get("alg")
    kid = header.get("kid")
    allowed_algs = {"RS256", "ES256"}
    if alg not in allowed_algs:
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=(
                "Unsupported JWT algorithm; expected one of "
                f"{sorted(allowed_algs)}, got {alg!r}."
            ),
        )
    if not isinstance(kid, str) or not kid.strip():
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail="JWT header did not include a signing key id (kid).",
        )

    try:
        jwks = _get_cached_jwks(jwks_url=jwks_url, ttl_seconds=300)
        jwk = _select_jwk(jwks=jwks, kid=kid)
        if jwk is None:
            # Clear diagnostic: wrong project URL or rotated keys without refresh.
            raise ProblemException(
                status=401,
                code=ErrorCode.UNAUTHORIZED,
                detail=(
                    "JWT signing key id (kid) was not found in Supabase JWKS. "
                    f"kid={kid!r}, alg={alg!r}, jwks_url={jwks_url}."
                ),
            )
        signing_key = _public_key_from_jwk(jwk=jwk, alg=alg)
    except ProblemException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.exception(
            "Failed to resolve Supabase signing key (jwks_url=%s, kid=%r, alg=%r): %s",
            jwks_url,
            kid,
            alg,
            e,
        )
        raise ProblemException(
            status=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=(
                "Unable to fetch or resolve signing key from Supabase JWKS. "
                f"jwks_url={jwks_url}, kid={kid!r}, alg={alg!r}, cause={type(e).__name__}."
            ),
        ) from e

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
            algorithms=[alg],
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
    payload = _jwt_verify_supabase_jwt(token)
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
