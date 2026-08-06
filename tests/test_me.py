"""Tests for current-user role resolution."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.schemas.domain import MeResponse


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


def test_me_dev_identity_rejects_unknown_role(client: TestClient) -> None:
    """Unknown development roles fall back to the safe default role."""
    response = client.get(
        "/v1/me",
        headers={"X-User-Role": "UnknownRole", "X-User-Name": "Test User"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "PlantManager"


def test_me_bearer_token_does_not_fall_back_to_dev_identity(client: TestClient) -> None:
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
