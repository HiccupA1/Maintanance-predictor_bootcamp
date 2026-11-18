"""Tests for current-user role resolution."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.routers import me
from app.core.config import Settings
from app.schemas.domain import MeResponse


@pytest.fixture
def dev_shim(monkeypatch):
    """Run /me with APP_ENV=dev and the identity shim enabled."""
    monkeypatch.setattr(
        me,
        "get_settings",
        lambda: Settings(app_env="dev", enable_dev_identity_shim=True),
    )


def test_settings_default_to_production_without_shim(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENABLE_DEV_IDENTITY_SHIM", raising=False)
    settings = Settings(_env_file=None)
    assert settings.app_env == "production"
    assert settings.enable_dev_identity_shim is False


@pytest.mark.parametrize("app_env", ["test", "staging", "production"])
def test_shim_is_refused_outside_dev(app_env: str) -> None:
    with pytest.raises(ValidationError, match="APP_ENV=dev"):
        Settings(
            _env_file=None, app_env=app_env, enable_dev_identity_shim=True
        )


def test_me_without_token_is_401_when_shim_disabled(
    client: TestClient,
) -> None:
    response = client.get("/v1/me", headers={"X-User-Role": "Admin"})
    assert response.status_code == 401


@pytest.mark.usefixtures("dev_shim")
def test_me_dev_identity_returns_selected_role(client: TestClient) -> None:
    """The development identity shim returns the role supplied by the header."""
    for role in ("Admin", "PlantManager", "Operator", "MaintenanceEngineer"):
        response = client.get(
            "/v1/me",
            headers={"X-User-Role": role, "X-User-Name": f"{role} User"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "user_id": "dev",
            "name": f"{role} User",
            "role": role,
        }


@pytest.mark.usefixtures("dev_shim")
def test_me_dev_identity_rejects_unknown_role(client: TestClient) -> None:
    """Unknown development roles fall back to the safe default role."""
    response = client.get(
        "/v1/me",
        headers={"X-User-Role": "UnknownRole", "X-User-Name": "Test User"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "PlantManager"


@pytest.mark.usefixtures("dev_shim")
def test_me_bearer_token_does_not_fall_back_to_dev_identity(
    client: TestClient,
) -> None:
    """Bearer tokens must not be ignored in favor of the DEV identity shim."""
    response = client.get(
        "/v1/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_me_response_coerces_uuid_user_id_to_str() -> None:
    """MeResponse should accept UUID inputs and serialize `user_id` as a string."""
    user_id = UUID("80011a9a-2320-4e2a-a75c-49e0d419b144")
    model = MeResponse(user_id=user_id, name="User", role="Operator")
    assert model.user_id == str(user_id)
