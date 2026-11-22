"""WP6 security review fixes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import Settings
from app.core.errors import ProblemException


def test_security_headers_on_every_response(client: TestClient) -> None:
    for path in ("/v1/health", "/v1/equipment"):  # public and 401 responses
        headers = client.get(path).headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["Referrer-Policy"] == "no-referrer"
        assert headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    ("env", "override", "expected"),
    [
        ("production", None, False),
        ("staging", None, True),
        ("dev", None, True),
        ("production", True, True),
    ],
)
def test_api_docs_off_in_production_by_default(
    env, override, expected
) -> None:
    settings = Settings(_env_file=None, app_env=env, api_docs_enabled=override)
    assert settings.docs_enabled is expected


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "http://evil.example/jwks"]
)
def test_non_https_jwks_refused_outside_dev(monkeypatch, url) -> None:
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(_env_file=None, app_env="production"),
    )
    with pytest.raises(ProblemException) as exc:
        auth._fetch_supabase_jwks(url)
    assert exc.value.status == 401
    assert url not in str(exc.value.detail)


def test_jwks_failure_detail_does_not_leak_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        auth, "get_settings", lambda: Settings(_env_file=None, app_env="test")
    )
    url = "http://127.0.0.1:9/never-listening/jwks.json"
    with pytest.raises(ProblemException) as exc:
        auth._fetch_supabase_jwks(url)
    detail = str(exc.value.detail)
    assert "127.0.0.1" not in detail and "jwks" not in detail.lower()


def test_oversized_reading_value_rejected(client: TestClient, as_role) -> None:
    as_role("Operator")
    resp = client.post(
        "/v1/readings",
        json={
            "equipment_id": "eq-1111",
            "parameter_id": "x",
            "value": "9" * 257,
        },
    )
    assert resp.status_code == 422
