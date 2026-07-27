"""Tests for health endpoints."""

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    """GET /health returns the expected liveness payload."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_db_ok(client: TestClient) -> None:
    """GET /health/db confirms database connectivity."""
    resp = client.get("/health/db")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
