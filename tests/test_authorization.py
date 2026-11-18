"""Route-by-route authorization tests.

``ROUTE_PERMISSIONS`` must list every API route. The completeness test fails
when a route is added without an entry here, so a new route cannot ship
without a decision about who may call it. Each entry is then checked for:

- no credentials -> 401
- each role outside the policy -> 403
- each role inside the policy -> passes authorization (any status except
  401/403; the request may still be 404/422 because the test sends
  placeholder ids and empty bodies)
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.rbac import POLICY, Permission, Role
from app.main import app

P = Permission

ROUTE_PERMISSIONS: dict[tuple[str, str], Permission] = {
    ("GET", "/v1/equipment"): P.EQUIPMENT_READ,
    ("POST", "/v1/equipment"): P.EQUIPMENT_WRITE,
    ("GET", "/v1/equipment/{equipment_id}"): P.EQUIPMENT_READ,
    ("PUT", "/v1/equipment/{equipment_id}"): P.EQUIPMENT_WRITE,
    ("DELETE", "/v1/equipment/{equipment_id}"): P.EQUIPMENT_DELETE,
    ("GET", "/v1/equipment/{equipment_id}/parameters"): P.PARAMETER_READ,
    ("POST", "/v1/equipment/{equipment_id}/parameters"): P.PARAMETER_WRITE,
    ("PUT", "/v1/parameters/{parameter_id}"): P.PARAMETER_WRITE,
    ("POST", "/v1/readings"): P.READING_WRITE,
    (
        "GET",
        "/v1/equipment/{equipment_id}/parameters/{parameter_id}/readings",
    ): P.READING_READ,
    ("PUT", "/v1/readings/{reading_id}"): P.READING_WRITE,
    ("DELETE", "/v1/readings/{reading_id}"): P.READING_WRITE,
    ("GET", "/v1/alerts"): P.ALERT_READ,
    ("GET", "/v1/alerts/{alert_id}"): P.ALERT_READ,
    ("DELETE", "/v1/alerts/{alert_id}"): P.ALERT_DELETE,
    ("GET", "/v1/work-orders"): P.WORK_ORDER_READ,
    ("POST", "/v1/work-orders"): P.WORK_ORDER_CREATE,
    ("GET", "/v1/work-orders/{work_order_id}"): P.WORK_ORDER_READ,
    ("PUT", "/v1/work-orders/{work_order_id}"): P.WORK_ORDER_UPDATE,
    ("DELETE", "/v1/work-orders/{work_order_id}"): P.WORK_ORDER_DELETE,
    ("GET", "/v1/admin/users"): P.USER_ADMIN,
    ("POST", "/v1/admin/users"): P.USER_ADMIN,
    ("PUT", "/v1/admin/users/{supabase_user_id}"): P.USER_ADMIN,
    ("DELETE", "/v1/admin/users/{supabase_user_id}"): P.USER_ADMIN,
    ("PUT", "/v1/admin/users/{supabase_user_id}/role"): P.USER_ADMIN,
    ("GET", "/v1/equipment/{equipment_id}/risk"): P.RISK_READ,
    ("GET", "/v1/models"): P.MODEL_ADMIN,
    ("POST", "/v1/models/{model_id}/stage"): P.MODEL_ADMIN,
}

# Deliberately unauthenticated routes, with the reason.
PUBLIC_ROUTES: dict[tuple[str, str], str] = {
    ("GET", "/v1/health"): "liveness probe",
    ("GET", "/v1/health/db"): "readiness probe",
    # /me resolves the caller's own identity: it requires a valid token
    # (or the APP_ENV=dev shim) and is covered in tests/test_me.py.
    ("GET", "/v1/me"): "identity; see test_me.py",
}

PLACEHOLDER_ID = "00000000-0000-0000-0000-000000000000"


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _api_routes() -> set[tuple[str, str]]:
    """Every (method, path) the app serves, from its public OpenAPI schema."""
    return {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method in HTTP_METHODS
    }


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", PLACEHOLDER_ID, path)


def _request(client: TestClient, method: str, path: str):
    kwargs = {"json": {}} if method in {"POST", "PUT"} else {}
    return client.request(method, _concrete(path), **kwargs)


@pytest.fixture
def client() -> TestClient:
    # Authorized requests may still hit unrelated open defects (e.g. D8 on
    # GET /alerts returns 500); return the response rather than raising so
    # these tests assert on authorization only.
    return TestClient(app, raise_server_exceptions=False)


def test_every_route_has_an_authorization_decision() -> None:
    declared = set(ROUTE_PERMISSIONS) | set(PUBLIC_ROUTES)
    actual = _api_routes()
    assert actual - declared == set(), "routes missing from ROUTE_PERMISSIONS"
    assert declared - actual == set(), "stale entries in ROUTE_PERMISSIONS"
    assert set(ROUTE_PERMISSIONS).isdisjoint(PUBLIC_ROUTES)


@pytest.mark.parametrize(
    ("method", "path"),
    sorted(ROUTE_PERMISSIONS),
    ids=[f"{m} {p}" for m, p in sorted(ROUTE_PERMISSIONS)],
)
def test_unauthenticated_request_is_rejected(
    client: TestClient, method: str, path: str
) -> None:
    response = _request(client, method, path)
    assert response.status_code == 401, response.text
    assert response.json()["code"] == "unauthorized"


def _role_cases(allowed: bool):
    for (method, path), permission in sorted(ROUTE_PERMISSIONS.items()):
        for role in Role:
            if (role in POLICY[permission]) is allowed:
                yield pytest.param(
                    method,
                    path,
                    role.value,
                    id=f"{method} {path} {role.value}",
                )


@pytest.mark.parametrize(("method", "path", "role"), _role_cases(False))
def test_role_outside_policy_is_forbidden(
    client: TestClient, as_role, method: str, path: str, role: str
) -> None:
    as_role(role)
    response = _request(client, method, path)
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "forbidden"


@pytest.mark.parametrize(("method", "path", "role"), _role_cases(True))
def test_role_inside_policy_passes_authorization(
    client: TestClient, as_role, method: str, path: str, role: str
) -> None:
    as_role(role)
    response = _request(client, method, path)
    assert response.status_code not in {401, 403}, response.text


def test_unknown_role_is_forbidden(client: TestClient, as_role) -> None:
    as_role("Superuser")
    assert client.get("/v1/equipment").status_code == 403


def test_reading_author_comes_from_the_token_not_a_header(
    client: TestClient, as_role
) -> None:
    from app.db.session import SessionLocal
    from tests.test_endpoint_serialization_regressions import (
        _seed_equipment_with_parameter,
    )

    db = SessionLocal()
    equipment_id, _pk, parameter_id = _seed_equipment_with_parameter(db)
    db.close()

    as_role("Operator", name="Verified Operator")
    response = client.post(
        "/v1/readings",
        headers={"X-User-Name": "Spoofed Name"},
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "5",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["entered_by"] == "Verified Operator"
