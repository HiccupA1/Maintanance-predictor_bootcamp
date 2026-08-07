"""Tests for equipment endpoints."""

from __future__ import annotations

from uuid import uuid4

from app.schemas.domain import EquipmentListResponse


def test_equipment_list_response_coerces_uuid_id_to_str() -> None:
    """Ensure API schema accepts UUID ids and serializes them as strings.

    Regression test for GET /v1/equipment 500 caused by EquipmentResponse.id
    expecting `str` while persistence returned `uuid.UUID`.
    """
    raw_id = uuid4()
    payload = {
        "items": [
            {
                "id": raw_id,
                "equipment_id": "EQ-100",
                "name": "Compressor A",
                "location": "Plant 1",
                "type": "Compressor",
                "criticality": 3,
                "last_service_date": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ],
        "total": 1,
    }

    parsed = EquipmentListResponse.model_validate(payload)
    assert parsed.items[0].id == str(raw_id)
