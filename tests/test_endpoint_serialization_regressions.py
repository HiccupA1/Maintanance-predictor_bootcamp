"""Integration-style endpoint serialization regressions.

These tests exercise FastAPI response_model validation end-to-end for a few key
endpoints that return ORM objects directly (or ORM lists). They are intended to
catch ResponseValidationError-driven HTTP 500s caused by ORM/Pydantic type
mismatches.
"""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.models.equipment import Equipment, Parameter, Reading


def _seed_equipment_with_parameter(db) -> tuple[str, str, str]:
    """Create and persist an equipment + parameter; return (equipment_id, parameter_id)."""
    equipment = Equipment(
        equipment_id="EQ-INT-1",
        name="Pump Integration",
        location="Plant 1",
        type="Pump",
        criticality=3,
    )
    db.add(equipment)
    db.flush()

    parameter = Parameter(
        equipment_id=equipment.id,
        name="Vibration",
        unit="mm/s",
        max_threshold=10.0,
    )
    db.add(parameter)
    db.flush()
    db.commit()

    # IMPORTANT:
    # - API routes under /v1/equipment/{equipment_id} expect the *business* id
    #   (Equipment.equipment_id), not the PK (Equipment.id).
    # - FK fields (Parameter.equipment_id, Reading.equipment_id) reference the PK.
    return str(equipment.equipment_id), str(equipment.id), str(parameter.id)


def test_list_parameters_serializes_cleanly_and_includes_correlation_id_header(
    client: TestClient,
) -> None:
    """GET /v1/equipment/{id}/parameters returns 200, JSON list, and X-Correlation-Id."""
    # Use the same DB session wiring as the app/TestClient via the conftest
    # fixture seeding (shared engine) to avoid sqlite in-memory visibility issues.
    from app.db.session import SessionLocal

    db = SessionLocal()
    equipment_business_id, _equipment_pk, _parameter_id = _seed_equipment_with_parameter(db)
    db.close()

    resp = client.get(f"/v1/equipment/{equipment_business_id}/parameters")
    assert resp.status_code == 200, resp.text
    assert "X-Correlation-Id" in resp.headers
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    # Response equipment_id is the Equipment PK (FK in parameters), not the business id.
    assert body[0]["equipment_id"] != equipment_business_id
    assert body[0]["name"] == "Vibration"
    assert "created_at" in body[0]
    assert "updated_at" in body[0]


def test_create_reading_serializes_cleanly(client: TestClient) -> None:
    """POST /v1/readings returns 201 and a valid JSON body."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    equipment_business_id, equipment_pk, parameter_id = _seed_equipment_with_parameter(db)
    db.close()

    resp = client.post(
        "/v1/readings",
        headers={"X-User-Name": "Integration Tester"},
        json={
            # ReadingCreate.equipment_id is the *business* id (Equipment.equipment_id).
            "equipment_id": equipment_business_id,
            "parameter_id": parameter_id,
            "value": "9.9",
            # include explicit timestamp; schema normalization should handle it
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Response `equipment_id` is the FK to Equipment PK (Reading.equipment_id), not the business id.
    assert body["equipment_id"] == equipment_pk
    assert body["parameter_id"] == parameter_id
    assert body["value"] == "9.9"
    assert body["entered_by"] == "Integration Tester"
    assert "timestamp" in body


def test_list_readings_serializes_cleanly(client: TestClient) -> None:
    """GET readings list returns 200 and JSON list (no response validation 500s)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    equipment_business_id, equipment_pk, parameter_id = _seed_equipment_with_parameter(db)
    db.add(
        Reading(
            equipment_id=equipment_pk,
            parameter_id=parameter_id,
            value="9.5",
            timestamp=datetime(2026, 1, 1, 0, 0, 0),
            entered_by="Seeder",
        )
    )
    db.commit()
    db.close()

    resp = client.get(
        f"/v1/equipment/{equipment_business_id}/parameters/{parameter_id}/readings"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["equipment_id"] == equipment_pk
    assert body[0]["parameter_id"] == parameter_id
    assert "timestamp" in body[0]


def test_list_alerts_serializes_cleanly(client: TestClient) -> None:
    """GET /v1/alerts returns 200 and list JSON (covers AlertResponse validators)."""
    resp = client.get("/v1/alerts")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    # conftest seeds at least two alerts
    assert len(body) >= 2
    assert "id" in body[0]
    assert "equipment_id" in body[0]
    assert "created_at" in body[0]
    assert "updated_at" in body[0]
