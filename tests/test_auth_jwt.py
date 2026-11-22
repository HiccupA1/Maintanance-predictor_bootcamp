"""Regression tests for Supabase JWT verification (app/core/auth.py).

Tokens are signed with locally generated RSA and EC keys, and the JWKS fetch is
stubbed. This covers the security-critical paths independently of the PyJWT
and cryptography versions, so dependency upgrades are verified here.
"""

from __future__ import annotations

import json
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import Settings
from app.core.errors import ProblemException

RSA_KID = "test-rsa-key"
EC_KID = "test-ec-key"


@pytest.fixture(scope="module")
def keys():
    """Generate one RSA and one EC P-256 signing key for the module."""
    return {
        RSA_KID: rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        ),
        EC_KID: ec.generate_private_key(ec.SECP256R1()),
    }


@pytest.fixture(autouse=True)
def stub_jwks(monkeypatch, keys):
    """Serve the test public keys as the Supabase JWKS."""
    jwks = {
        "keys": [
            {
                **json.loads(
                    jwt.algorithms.RSAAlgorithm.to_jwk(
                        keys[RSA_KID].public_key()
                    )
                ),
                "kid": RSA_KID,
                "alg": "RS256",
                "use": "sig",
            },
            {
                **json.loads(
                    jwt.algorithms.ECAlgorithm.to_jwk(
                        keys[EC_KID].public_key()
                    )
                ),
                "kid": EC_KID,
                "alg": "ES256",
                "use": "sig",
            },
        ]
    }
    monkeypatch.setattr(
        auth, "_supabase_jwks_url", lambda: "https://test.invalid/jwks"
    )
    monkeypatch.setattr(auth, "_fetch_supabase_jwks", lambda _url: jwks)
    auth._JWKS_CACHE.update({"expires_at": 0.0, "jwks": None, "url": ""})
    yield
    auth._JWKS_CACHE.update({"expires_at": 0.0, "jwks": None, "url": ""})


def _token(keys, kid=RSA_KID, alg="RS256", **overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "operator@example.com",
        "aud": "authenticated",
        "iat": now,
        "exp": now + 300,
        **overrides,
    }
    return jwt.encode(claims, keys[kid], algorithm=alg, headers={"kid": kid})


def _assert_unauthorized(token: str) -> str:
    with pytest.raises(ProblemException) as exc:
        auth._jwt_verify_supabase_jwt(token)
    assert exc.value.status == 401
    return str(exc.value.detail)


@pytest.mark.parametrize(
    ("kid", "alg"), [(RSA_KID, "RS256"), (EC_KID, "ES256")]
)
def test_valid_token_is_accepted(keys, kid, alg) -> None:
    claims = auth._jwt_verify_supabase_jwt(_token(keys, kid=kid, alg=alg))
    assert claims["email"] == "operator@example.com"


def test_expired_token_is_rejected(keys) -> None:
    past = int(time.time()) - 3600
    detail = _assert_unauthorized(_token(keys, iat=past - 60, exp=past))
    assert "expired" in detail.lower()


def test_tampered_payload_is_rejected(keys) -> None:
    header, _payload, signature = _token(keys).split(".")
    forged = jwt.utils.base64url_encode(
        json.dumps({"sub": "attacker", "exp": int(time.time()) + 300}).encode()
    ).decode()
    _assert_unauthorized(f"{header}.{forged}.{signature}")


def test_token_signed_by_unknown_key_is_rejected(keys) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {"sub": "x", "exp": int(time.time()) + 300},
        other,
        algorithm="RS256",
        headers={"kid": RSA_KID},
    )
    _assert_unauthorized(token)


def test_unknown_kid_is_rejected(keys) -> None:
    token = jwt.encode(
        {"sub": "x", "exp": int(time.time()) + 300},
        keys[RSA_KID],
        algorithm="RS256",
        headers={"kid": "rotated-away"},
    )
    assert "kid" in _assert_unauthorized(token)


def test_symmetric_algorithm_is_rejected() -> None:
    # Algorithm-confusion guard: HS256 must never be accepted, whatever key.
    token = jwt.encode(
        {"sub": "x", "exp": int(time.time()) + 300},
        "a-shared-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
        headers={"kid": RSA_KID},
    )
    assert "algorithm" in _assert_unauthorized(token).lower()


def test_unsigned_token_is_rejected(keys) -> None:
    token = jwt.encode(
        {"sub": "x", "exp": int(time.time()) + 300},
        None,
        algorithm="none",
        headers={"kid": RSA_KID},
    )
    _assert_unauthorized(token)


def test_audience_is_enforced_when_configured(keys, monkeypatch) -> None:
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(supabase_jwt_audience="authenticated"),
    )
    auth._jwt_verify_supabase_jwt(_token(keys))  # matching audience
    _assert_unauthorized(_token(keys, aud="some-other-service"))


def test_me_with_valid_token_provisions_operator_profile(
    client: TestClient, keys
) -> None:
    subject = str(uuid.uuid4())
    response = client.get(
        "/v1/me",
        headers={"Authorization": f"Bearer {_token(keys, sub=subject)}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "Operator"  # default role for first-seen users


def test_me_with_expired_token_returns_401(client: TestClient, keys) -> None:
    past = int(time.time()) - 3600
    response = client.get(
        "/v1/me",
        headers={
            "Authorization": f"Bearer {_token(keys, iat=past - 60, exp=past)}"
        },
    )
    assert response.status_code == 401
