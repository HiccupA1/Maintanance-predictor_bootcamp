"""Tests for current-user role resolution."""

from fastapi.testclient import TestClient


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
