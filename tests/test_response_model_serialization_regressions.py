"""Regression tests for response-model serialization against ORM-like objects.

These tests target the specific failure mode that triggered 500s:
Pydantic v2 response models declared `str` ids / `datetime` timestamps, while the
persistence layer (or driver/backend variance) can materialize UUIDs and
timezone-naive datetimes. The response schema validators must coerce/normalize
these values so FastAPI response validation does not raise ValidationError.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.domain import AlertResponse, ParameterResponse, ReadingResponse
from app.schemas.work_orders import WorkOrder, WorkOrderPartLine, WorkOrderSummary


def _naive_dt() -> datetime:
    """Return a deterministic tz-naive datetime used for normalization tests."""
    return datetime(2026, 1, 2, 3, 4, 5)


def test_parameter_response_model_validate_coerces_uuid_and_normalizes_datetimes() -> None:
    """ParameterResponse accepts UUID ids and tz-naive created/updated timestamps."""
    raw_id = uuid4()
    raw_equipment_id = uuid4()
    payload = {
        "id": raw_id,
        "equipment_id": raw_equipment_id,
        "name": "Temperature",
        "unit": "C",
        "min_threshold": None,
        "max_threshold": 90.0,
        "active": True,
        "suggested_action": None,
        "created_at": _naive_dt(),
        "updated_at": _naive_dt(),
    }

    model = ParameterResponse.model_validate(payload)
    assert model.id == str(raw_id)
    assert model.equipment_id == str(raw_equipment_id)
    assert model.created_at.tzinfo is not None
    assert model.updated_at.tzinfo is not None

    # Must be JSON-serializable with no ValidationError.
    dumped = model.model_dump(mode="json")
    assert dumped["id"] == str(raw_id)
    assert dumped["equipment_id"] == str(raw_equipment_id)
    assert isinstance(dumped["created_at"], str)
    assert isinstance(dumped["updated_at"], str)


def test_reading_response_model_validate_coerces_uuid_and_normalizes_timestamps() -> None:
    """ReadingResponse accepts UUID ids/foreign keys and tz-naive timestamps."""
    raw_id = uuid4()
    raw_equipment_id = uuid4()
    raw_parameter_id = uuid4()
    payload = {
        "id": raw_id,
        "equipment_id": raw_equipment_id,
        "parameter_id": raw_parameter_id,
        "value": "12.3",
        "timestamp": _naive_dt(),
        "entered_by": "dev",
        "modified_by": None,
        "modified_at": _naive_dt(),
        "modification_reason": None,
    }

    model = ReadingResponse.model_validate(payload)
    assert model.id == str(raw_id)
    assert model.equipment_id == str(raw_equipment_id)
    assert model.parameter_id == str(raw_parameter_id)
    assert model.timestamp.tzinfo is not None
    assert model.modified_at is not None and model.modified_at.tzinfo is not None

    dumped = model.model_dump(mode="json")
    assert dumped["id"] == str(raw_id)
    assert dumped["equipment_id"] == str(raw_equipment_id)
    assert dumped["parameter_id"] == str(raw_parameter_id)
    assert isinstance(dumped["timestamp"], str)
    assert isinstance(dumped["modified_at"], str)


def test_alert_response_model_validate_coerces_optional_uuid_and_normalizes_datetimes() -> None:
    """AlertResponse preserves None optionals while coercing UUIDs and normalizing times."""
    raw_id = uuid4()
    raw_equipment_id = uuid4()
    raw_parameter_id = uuid4()

    payload = {
        "id": raw_id,
        "equipment_id": raw_equipment_id,
        "equipment_name": None,
        "parameter_id": raw_parameter_id,
        "parameter_name": None,
        "status": "NEW",
        "priority": "HIGH",
        "current_value": "9.5",
        "breach_timestamp": _naive_dt(),
        "min_threshold": None,
        "max_threshold": 10.0,
        "suggested_action": None,
        "why_priority": None,
        "created_at": _naive_dt(),
        "updated_at": _naive_dt(),
    }

    model = AlertResponse.model_validate(payload)
    assert model.id == str(raw_id)
    assert model.equipment_id == str(raw_equipment_id)
    assert model.parameter_id == str(raw_parameter_id)
    assert model.breach_timestamp is not None and model.breach_timestamp.tzinfo is not None
    assert model.created_at.tzinfo is not None
    assert model.updated_at.tzinfo is not None

    dumped = model.model_dump(mode="json")
    assert dumped["id"] == str(raw_id)
    assert dumped["equipment_id"] == str(raw_equipment_id)
    assert dumped["parameter_id"] == str(raw_parameter_id)
    assert isinstance(dumped["created_at"], str)
    assert isinstance(dumped["updated_at"], str)


def test_work_order_models_accept_orm_like_objects_with_uuid_and_naive_datetimes() -> None:
    """WorkOrder/WorkOrderSummary/WorkOrderPartLine validate from ORM-like attributes."""
    raw_work_order_id = uuid4()
    raw_alert_id = uuid4()
    raw_equipment_id = uuid4()
    raw_part_line_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    part = SimpleNamespace(id=raw_part_line_id, part_name="N/A", used=False, notes=None)

    orm_like = SimpleNamespace(
        id=raw_work_order_id,
        alert_id=raw_alert_id,
        equipment_id=raw_equipment_id,
        equipment_name="Pump A",
        work_order_number=1,
        description="Inspect and repair",
        priority=" high ",
        status=" open ",
        issuer_name="Alice",
        due_at=_naive_dt(),
        machine_details={"model": "PUMP-X"},
        readings_snapshot={"vibration": 9.5},
        resolution_notes=None,
        root_cause=None,
        closed_at=None,
        closed_by=None,
        created_at=_naive_dt(),
        updated_at=_naive_dt(),
        parts=[part],
    )

    full = WorkOrder.model_validate(orm_like)
    assert full.id == str(raw_work_order_id)
    assert full.alert_id == str(raw_alert_id)
    assert full.equipment_id == str(raw_equipment_id)
    assert full.priority.value == "HIGH"
    assert full.status.value == "OPEN"
    assert full.created_at.tzinfo is not None
    assert full.updated_at.tzinfo is not None
    assert full.due_at is not None and full.due_at.tzinfo is not None
    assert full.parts[0].id == str(raw_part_line_id)

    summary_like = SimpleNamespace(
        id=raw_work_order_id,
        alert_id=raw_alert_id,
        equipment_id=raw_equipment_id,
        equipment_name="Pump A",
        work_order_number=1,
        priority=" medium ",
        status=" open ",
        due_at=None,
        created_at=_naive_dt(),
    )
    summary = WorkOrderSummary.model_validate(summary_like)
    assert summary.id == str(raw_work_order_id)
    assert summary.created_at.tzinfo is not None
    assert summary.priority.value == "MEDIUM"
    assert summary.status.value == "OPEN"

    # Ensure JSON dumps succeed (the end goal for API serialization).
    assert isinstance(full.model_dump(mode="json")["created_at"], str)
    assert isinstance(summary.model_dump(mode="json")["created_at"], str)


def test_work_order_part_line_model_validate_coerces_uuid_id_to_str() -> None:
    """WorkOrderPartLine alone coerces UUID ids when validating from attributes."""
    raw_part_line_id = uuid4()
    orm_like = SimpleNamespace(id=raw_part_line_id, part_name="Filter", used=True, notes="ok")

    model = WorkOrderPartLine.model_validate(orm_like)
    assert model.id == str(raw_part_line_id)
    dumped = model.model_dump(mode="json")
    assert dumped["id"] == str(raw_part_line_id)
