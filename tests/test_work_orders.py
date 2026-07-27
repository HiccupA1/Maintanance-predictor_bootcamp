"""Tests for the Work Order endpoints and business rules.

Covers the contract's required scenarios:

* create success (201) with a valid alert (and alert transition to IN_PROGRESS)
* duplicate work order for the same alert (409 duplicate_work_order)
* update a closed work order rejected (409 invalid_state)
* update with an empty body rejected (422 invalid_request)
* fetch a non-existent work order (404 work_order_not_found)
* create against a non-existent alert (404 alert_not_found)
* list with invalid page/page_size or invalid from/to (422 invalid_request)
* list happy path with pagination
"""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.alert import Alert
from tests.conftest import SEEDED_ALERT_ID, SECOND_ALERT_ID


def _create_payload(**overrides) -> dict:
    """Build a valid create payload, applying optional overrides."""
    payload = {
        "description": "Inspect and repair pump vibration",
        "priority": "HIGH",
    }
    payload.update(overrides)
    return payload


def test_create_work_order_success(client: TestClient) -> None:
    """Creating a work order for a valid alert returns 201 and transitions."""
    resp = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["alert_id"] == SEEDED_ALERT_ID
    assert body["equipment_id"] == "eq-1111"
    assert body["priority"] == "HIGH"
    assert body["status"] == "OPEN"
    # Snapshot fields inherited from the alert.
    assert body["issuer_name"] == "Alice Operator"
    assert body["machine_details"] == {"model": "PUMP-X"}

    # The alert must have transitioned to IN_PROGRESS in the same transaction.
    db = SessionLocal()
    try:
        alert = db.get(Alert, SEEDED_ALERT_ID)
        assert alert.status == "IN_PROGRESS"
    finally:
        db.close()


def test_create_duplicate_work_order_conflict(client: TestClient) -> None:
    """A second work order for the same alert returns 409 duplicate."""
    first = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    )
    assert first.status_code == 201
    second = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    )
    assert second.status_code == 409
    problem = second.json()
    assert problem["code"] == "duplicate_work_order"
    # Envelope shape assertions.
    for key in ("type", "title", "status", "code", "instance"):
        assert key in problem


def test_create_work_order_alert_not_found(client: TestClient) -> None:
    """Creating against an unknown alert returns 404 alert_not_found."""
    resp = client.post(
        "/v1/alerts/99999999-9999-9999-9999-999999999999/work-orders",
        json=_create_payload(),
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "alert_not_found"


def test_update_closed_work_order_rejected(client: TestClient) -> None:
    """Updating a CLOSED work order returns 409 invalid_state."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    wo_id = created["id"]

    # Close the work order.
    close = client.put(
        f"/v1/work-orders/{wo_id}",
        json={
            "status": "CLOSED",
            "resolution_notes": "Replaced bearing",
            "root_cause": "Worn bearing",
        },
    )
    assert close.status_code == 200
    assert close.json()["status"] == "CLOSED"

    # Any subsequent update must be rejected.
    resp = client.put(
        f"/v1/work-orders/{wo_id}", json={"description": "reopen attempt"}
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_state"


def test_update_empty_body_rejected(client: TestClient) -> None:
    """A no-op (empty) update body returns 422 invalid_request."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    resp = client.put(f"/v1/work-orders/{created['id']}", json={})
    assert resp.status_code == 422
    assert resp.json()["code"] == "invalid_request"


def test_update_work_order_success(client: TestClient) -> None:
    """A valid partial update applies and returns the updated work order."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    resp = client.put(
        f"/v1/work-orders/{created['id']}",
        json={"priority": "CRITICAL", "description": "Escalated repair"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["priority"] == "CRITICAL"
    assert body["description"] == "Escalated repair"


def test_get_nonexistent_work_order(client: TestClient) -> None:
    """Fetching an unknown work order returns 404 work_order_not_found."""
    resp = client.get("/v1/work-orders/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["code"] == "work_order_not_found"


def test_get_work_order_success(client: TestClient) -> None:
    """Fetching an existing work order returns 200 with its data."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    resp = client.get(f"/v1/work-orders/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_create_invalid_priority_rejected(client: TestClient) -> None:
    """A lowercase/invalid priority is rejected as 422 invalid_request."""
    resp = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders",
        json=_create_payload(priority="high"),
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "invalid_request"


def test_list_invalid_page_rejected(client: TestClient) -> None:
    """An invalid page (< 1) is rejected as 422 invalid_request."""
    resp = client.get("/v1/work-orders?page=0")
    assert resp.status_code == 422
    assert resp.json()["code"] == "invalid_request"


def test_list_invalid_time_window_rejected(client: TestClient) -> None:
    """created_from after created_to returns 422 invalid_request."""
    resp = client.get(
        "/v1/work-orders"
        "?created_from=2026-01-02T00:00:00Z&created_to=2026-01-01T00:00:00Z"
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "invalid_request"


def test_list_work_orders_pagination(client: TestClient) -> None:
    """Listing returns a paginated envelope with totals."""
    client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    )
    client.post(
        f"/v1/alerts/{SECOND_ALERT_ID}/work-orders",
        json=_create_payload(priority="MEDIUM"),
    )
    resp = client.get("/v1/work-orders?page=1&page_size=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1
    # Summary shape.
    item = body["items"][0]
    for key in ("id", "alert_id", "equipment_id", "priority", "status"):
        assert key in item
