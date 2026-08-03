"""Tests for admin user and role management endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from tests.conftest import client as client_fixture


def _seed_user(db: Session, supabase_user_id: str, role: str) -> None:
    db.add(
        UserProfile(
            supabase_user_id=supabase_user_id,
            email=f"{supabase_user_id}@example.com",
            display_name=supabase_user_id,
            role=role,
        )
    )
    db.commit()


def test_admin_list_requires_auth(client: TestClient) -> None:
    """GET /v1/admin/users requires auth and returns 401 without token."""
    resp = client.get("/v1/admin/users")
    assert resp.status_code == 401


def test_admin_list_forbidden_for_non_admin(
    client: TestClient, monkeypatch
) -> None:
    """GET /v1/admin/users returns 403 when current user role is not Admin."""
    # Monkeypatch auth dependency to bypass JWT and return a non-admin profile.
    from app.core import auth as auth_module

    def _fake_user():  # noqa: ANN001
        return UserProfile(
            supabase_user_id="user-1",
            email="user-1@example.com",
            display_name="User 1",
            role="Operator",
        )

    monkeypatch.setattr(auth_module, "get_current_user", lambda: _fake_user())
    resp = client.get("/v1/admin/users")
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
