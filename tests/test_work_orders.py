"""Tests for the Work Order endpoints and business rules."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.api.v1.routers import work_orders as work_orders_router
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.work_order import WorkOrder
from app.services import work_orders as work_orders_service
from tests.conftest import SECOND_ALERT_ID, SEEDED_ALERT_ID


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
    assert body["issuer_name"] == "Alice Operator"
    assert body["machine_details"] == {"model": "PUMP-X"}

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


def test_update_closed_work_order_requires_parts(client: TestClient) -> None:
    """Closing without a part line returns the required validation problem."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    close = client.put(
        f"/v1/work-orders/{created['id']}",
        json={
            "status": "CLOSED",
            "resolution_notes": "Replaced bearing",
            "root_cause": "Worn bearing",
        },
    )
    assert close.status_code == 422
    assert close.json()["code"] == "invalid_request"


def test_update_closed_work_order_success(client: TestClient) -> None:
    """Closing with an N/A part line resolves the alert."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    close = client.put(
        f"/v1/work-orders/{created['id']}",
        json={
            "status": "CLOSED",
            "resolution_notes": "Replaced bearing",
            "root_cause": "Worn bearing",
            "parts": [{"part_name": "N/A", "used": False}],
        },
    )
    assert close.status_code == 200
    assert close.json()["status"] == "CLOSED"

    db = SessionLocal()
    try:
        alert = db.get(Alert, SEEDED_ALERT_ID)
        assert alert.status == "RESOLVED"
    finally:
        db.close()

    response = client.put(
        f"/v1/work-orders/{created['id']}",
        json={"description": "reopen attempt"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "invalid_state"


def test_update_empty_body_rejected(client: TestClient) -> None:
    """A no-op empty update body returns 422 invalid_request."""
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
    """An invalid priority is rejected as 422 invalid_request."""
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


def test_detail_normalizes_persisted_enum_casing(
    client: TestClient, monkeypatch
) -> None:
    """Detail responses tolerate legacy casing and surrounding whitespace."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    db = SessionLocal()
    try:
        work_order = db.get(WorkOrder, created["id"])
        assert work_order is not None
        work_order.priority = " high "
        work_order.status = " open "
        monkeypatch.setattr(
            work_orders_service, "get_work_order", lambda *_args: work_order
        )
        response = client.get(f"/v1/work-orders/{created['id']}")
    finally:
        db.close()
    assert response.status_code == 200
    assert response.json()["priority"] == "HIGH"
    assert response.json()["status"] == "OPEN"


def test_list_normalizes_persisted_enum_casing(
    client: TestClient, monkeypatch
) -> None:
    """List summaries tolerate legacy casing and surrounding whitespace."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    db = SessionLocal()
    try:
        work_order = db.get(WorkOrder, created["id"])
        assert work_order is not None
        work_order.priority = " medium "
        work_order.status = " open "
        monkeypatch.setattr(
            work_orders_router,
            "service_list",
            lambda *_args, **_kwargs: ([work_order], 1),
        )
        response = client.get("/v1/work-orders")
    finally:
        db.close()
    assert response.status_code == 200
    assert response.json()["items"][0]["priority"] == "MEDIUM"
    assert response.json()["items"][0]["status"] == "OPEN"


def test_invalid_work_order_enum_is_rejected_by_database() -> None:
    """The database constraints prevent new invalid enum values."""
    db = SessionLocal()
    try:
        db.add(
            WorkOrder(
                alert_id=SECOND_ALERT_ID,
                equipment_id="eq-2222",
                description="Invalid enum test",
                priority="LOW",
                status="OPEN",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_invalid_response_enum_returns_data_integrity_problem(
    client: TestClient, monkeypatch
) -> None:
    """Unknown persisted values become an actionable Problem response."""
    created = client.post(
        f"/v1/alerts/{SEEDED_ALERT_ID}/work-orders", json=_create_payload()
    ).json()
    db = SessionLocal()
    try:
        work_order = db.get(WorkOrder, created["id"])
        assert work_order is not None
        work_order.priority = "LOW"
        monkeypatch.setattr(
            work_orders_service, "get_work_order", lambda *_args: work_order
        )
        response = client.get(f"/v1/work-orders/{created['id']}")
    finally:
        db.close()
    assert response.status_code == 500
    assert response.json()["code"] == "data_integrity_error"
