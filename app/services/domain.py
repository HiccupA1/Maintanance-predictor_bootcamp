"""Business services for equipment, parameters, readings, and alerts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter, Reading


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _not_found(detail: str) -> ProblemException:
    """Build a consistent domain not-found response."""
    return ProblemException(status=404, code=ErrorCode.INVALID_REQUEST, detail=detail)


def get_equipment(db: Session, equipment_id: str) -> Equipment:
    """Fetch equipment by its human-readable identifier."""
    row = db.execute(
        select(Equipment).where(Equipment.equipment_id == equipment_id)
    ).scalar_one_or_none()
    if row is None:
        raise _not_found(f"Equipment '{equipment_id}' does not exist.")
    return row


def get_parameter(db: Session, parameter_id: str) -> Parameter:
    """Fetch a parameter by id."""
    row = db.get(Parameter, parameter_id)
    if row is None:
        raise _not_found(f"Parameter '{parameter_id}' does not exist.")
    return row


def create_reading(
    db: Session, payload, entered_by: str
) -> Reading:
    """Persist a reading and synchronously update threshold alert state."""
    equipment = get_equipment(db, payload.equipment_id)
    parameter = get_parameter(db, payload.parameter_id)
    if parameter.equipment_id != equipment.id:
        raise ProblemException(
            status=422,
            code=ErrorCode.INVALID_REQUEST,
            detail="parameter_id does not belong to equipment_id.",
        )

    reading = Reading(
        equipment_id=equipment.id,
        parameter_id=parameter.id,
        value=payload.value,
        timestamp=payload.timestamp or _now(),
        entered_by=entered_by or "dev",
    )
    db.add(reading)

    numeric_value: float | None
    try:
        numeric_value = float(payload.value)
    except (TypeError, ValueError):
        numeric_value = None

    if parameter.active and numeric_value is not None:
        breached = (
            parameter.min_threshold is not None
            and numeric_value <= parameter.min_threshold
        ) or (
            parameter.max_threshold is not None
            and numeric_value >= parameter.max_threshold
        )
        active_alert = db.execute(
            select(Alert).where(
                Alert.equipment_id == equipment.id,
                Alert.parameter_id == parameter.id,
                Alert.status.in_(["NEW", "IN_PROGRESS"]),
            )
        ).scalar_one_or_none()

        if breached:
            if active_alert is None:
                active_alert = Alert(
                    equipment_id=equipment.id,
                    parameter_id=parameter.id,
                    status="NEW",
                    priority=(
                        "CRITICAL" if equipment.criticality >= 4 else "HIGH"
                    ),
                    current_value=reading.value,
                    breach_timestamp=reading.timestamp,
                    min_threshold=parameter.min_threshold,
                    max_threshold=parameter.max_threshold,
                    suggested_action=parameter.suggested_action,
                    why_priority=(
                        f"Value {reading.value} breached configured threshold."
                    ),
                )
                db.add(active_alert)
            else:
                active_alert.current_value = reading.value
                active_alert.breach_timestamp = reading.timestamp
        elif active_alert is not None:
            active_alert.status = "RESOLVED"

    db.commit()
    db.refresh(reading)
    return reading


def update_reading(
    db: Session, reading_id: str, payload, modified_by: str
) -> Reading:
    """Edit a reading only within five minutes of its original timestamp."""
    reading = db.get(Reading, reading_id)
    if reading is None:
        raise _not_found(f"Reading '{reading_id}' does not exist.")
    timestamp = reading.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if _now() > timestamp + timedelta(minutes=5):
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_STATE,
            detail="A reading can only be edited within five minutes of its timestamp.",
        )
    reading.value = payload.value
    reading.modified_by = modified_by or "dev"
    reading.modified_at = _now()
    reading.modification_reason = payload.modification_reason
    db.commit()
    db.refresh(reading)
    return reading
