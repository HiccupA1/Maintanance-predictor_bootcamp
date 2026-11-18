"""Work-order alert link (FR7), closure and labels (FR9-FR10), and D4."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.equipment import Equipment
from app.models.work_order import WorkOrder
from tests.conftest import SEEDED_ALERT_ID

CLOSE = {
    "status": "CLOSED",
    "resolution_notes": "Replaced bearing",
    "root_cause": "Bearing wear",
    "failure_confirmed": True,
    "failure_mode": "TWF",
}


@pytest.fixture(autouse=True)
def _plant_manager(as_role):
    as_role("PlantManager", name="Pat Manager")


def _from_alert(client: TestClient) -> dict:
    resp = client.post(
        "/v1/work-orders",
        json={
            "title": "Fix pump",
            "priority": "HIGH",
            "alert_id": SEEDED_ALERT_ID,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_page_size_200_with_legacy_rows_does_not_500(
    client: TestClient,
) -> None:
    """D4: one legacy enum value must not fail the whole page."""
    db = SessionLocal()
    db.add_all(
        WorkOrder(title=f"WO {i}", priority="HIGH", status="OPEN")
        for i in range(205)
    )
    db.add(WorkOrder(title="legacy", priority="low ", status="In Progress"))
    db.commit()
    db.close()

    resp = client.get("/v1/work-orders?page=1&page_size=200")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 206
    assert len(body["items"]) == 200


def test_work_order_from_alert_links_and_inherits_equipment(
    client: TestClient,
) -> None:
    wo = _from_alert(client)
    assert wo["alert_id"] == SEEDED_ALERT_ID
    assert wo["equipment_id"] == "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"


def test_second_work_order_for_same_alert_conflicts(
    client: TestClient,
) -> None:
    _from_alert(client)
    resp = client.post(
        "/v1/work-orders",
        json={
            "title": "Again",
            "priority": "HIGH",
            "alert_id": SEEDED_ALERT_ID,
        },
    )
    assert resp.status_code == 409


def test_unknown_alert_is_404(client: TestClient) -> None:
    resp = client.post(
        "/v1/work-orders",
        json={
            "title": "x",
            "priority": "HIGH",
            "alert_id": "99999999-9999-9999-9999-999999999999",
        },
    )
    assert resp.status_code == 404


def test_close_records_labels_and_resolves_alert(
    client: TestClient, as_role
) -> None:
    wo = _from_alert(client)
    as_role("MaintenanceEngineer", name="Mia Engineer")
    resp = client.put(f"/v1/work-orders/{wo['id']}", json=CLOSE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "CLOSED"
    assert body["failure_confirmed"] is True
    assert body["failure_mode"] == "TWF"
    assert body["closed_by"] == "Mia Engineer"
    assert body["closed_at"]

    db = SessionLocal()
    assert db.get(Alert, SEEDED_ALERT_ID).status == "RESOLVED"
    equipment = db.get(Equipment, "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1")
    assert equipment.last_service_date is not None
    db.close()


@pytest.mark.parametrize(
    ("drop", "field"),
    [
        ("resolution_notes", "resolution_notes"),
        ("root_cause", "root_cause"),
        ("failure_confirmed", "failure_confirmed"),
        ("failure_mode", "failure_mode"),
    ],
)
def test_close_requires_closure_fields(
    client: TestClient, drop: str, field: str
) -> None:
    wo = _from_alert(client)
    payload = {k: v for k, v in CLOSE.items() if k != drop}
    resp = client.put(f"/v1/work-orders/{wo['id']}", json=payload)
    assert resp.status_code == 422, resp.text
    assert resp.json()["errors"][0]["field"] == field


def test_no_failure_close_rejects_failure_mode(client: TestClient) -> None:
    wo = _from_alert(client)
    payload = {**CLOSE, "failure_confirmed": False}
    resp = client.put(f"/v1/work-orders/{wo['id']}", json=payload)
    assert resp.status_code == 422
    payload.pop("failure_mode")
    resp = client.put(f"/v1/work-orders/{wo['id']}", json=payload)
    assert resp.status_code == 200
    assert resp.json()["failure_mode"] is None


def test_labels_only_at_closure(client: TestClient) -> None:
    wo = _from_alert(client)
    resp = client.put(
        f"/v1/work-orders/{wo['id']}", json={"failure_confirmed": True}
    )
    assert resp.status_code == 422


def test_closed_work_order_is_immutable(client: TestClient) -> None:
    wo = _from_alert(client)
    client.put(f"/v1/work-orders/{wo['id']}", json=CLOSE)
    resp = client.put(f"/v1/work-orders/{wo['id']}", json={"title": "new"})
    assert resp.status_code == 409
