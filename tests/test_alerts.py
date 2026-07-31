"""Tests for alert API display fields."""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter


def test_list_alerts_includes_equipment_and_parameter_names(
    client: TestClient,
) -> None:
    """Alert list responses expose human-readable related-record labels."""
    db = SessionLocal()
    try:
        equipment = Equipment(
            equipment_id="PUMP-01",
            name="Cooling Pump A",
            location="Plant room",
            type="Pump",
            criticality=4,
        )
        db.add(equipment)
        db.flush()

        parameter = Parameter(
            equipment_id=equipment.id,
            name="Coolant temperature",
            unit="°C",
            max_threshold=90,
        )
        db.add(parameter)
        db.flush()

        db.add(
            Alert(
                equipment_id=equipment.id,
                parameter_id=parameter.id,
                status="NEW",
                priority="HIGH",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/v1/alerts")

    assert response.status_code == 200, response.text
    matching_alert = next(
        alert
        for alert in response.json()
        if alert["equipment_id"] == equipment.id
    )
    assert matching_alert["equipment_name"] == "Cooling Pump A"
    assert matching_alert["parameter_name"] == "Coolant temperature"
