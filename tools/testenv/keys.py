"""Signing key, JWKS file, access tokens and Supabase-shaped sessions."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

ROLES = ("Admin", "PlantManager", "Operator", "MaintenanceEngineer")
KID = "testenv-key"
TOKEN_TTL_S = 8 * 3600


def subject(role: str) -> str:
    """Stable user id per role, so reruns reuse the same profiles."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"testenv/{role}"))


def email(role: str) -> str:
    return f"{role.lower()}@testenv.invalid"


def display_name(role: str) -> str:
    return {
        "Admin": "Ada Admin",
        "PlantManager": "Pat Manager",
        "Operator": "Olu Operator",
        "MaintenanceEngineer": "Mia Engineer",
    }[role]


def write_keys(out: Path) -> rsa.RSAPrivateKey:
    """Generate a signing key and write its public JWKS to out/jwks.json."""
    out.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    (out / "jwks.json").write_text(
        json.dumps(
            {"keys": [{**jwk, "kid": KID, "alg": "RS256", "use": "sig"}]}
        )
    )
    return key


def access_token(key: rsa.RSAPrivateKey, role: str, now: int) -> str:
    return jwt.encode(
        {
            "sub": subject(role),
            "aud": "authenticated",
            "role": "authenticated",
            "email": email(role),
            "user_metadata": {"name": display_name(role)},
            "iat": now,
            "exp": now + TOKEN_TTL_S,
        },
        key,
        algorithm="RS256",
        headers={"kid": KID},
    )


def supabase_session(token: str, role: str, now: int) -> dict:
    """A session in the shape supabase-js persists to localStorage."""
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_S,
        "expires_at": now + TOKEN_TTL_S,
        "refresh_token": f"testenv-refresh-{role.lower()}",
        "user": {
            "id": subject(role),
            "aud": "authenticated",
            "role": "authenticated",
            "email": email(role),
            "app_metadata": {"provider": "email"},
            "user_metadata": {"name": display_name(role)},
            "created_at": "2026-01-01T00:00:00Z",
        },
    }


def write_credentials(key: rsa.RSAPrivateKey, out: Path) -> dict[str, str]:
    """Write tokens.json and sessions.json for every role."""
    now = int(time.time())
    tokens = {role: access_token(key, role, now) for role in ROLES}
    sessions = {
        role: supabase_session(tokens[role], role, now) for role in ROLES
    }
    (out / "tokens.json").write_text(json.dumps(tokens))
    (out / "sessions.json").write_text(json.dumps(sessions))
    return tokens
