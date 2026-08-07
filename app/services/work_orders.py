"""Work order service layer (live Supabase schema aligned).

This module intentionally implements *only* business logic that is supported by
the reconciled ORM model `app.models.work_order.WorkOrder` and the live Supabase
`public.work_orders` table.

Key schema facts (per reconciled ORM):
- `work_orders` has NO `alert_id` column (alerts and work_orders are not FK-linked).
- No `WorkOrderPartLine` table/model exists; there are no persisted part lines.
- No closure fields like `resolution_notes`, `root_cause`, `closed_at` exist.

The API may still expose a legacy UX route "create from alert"; if used, we treat
it as a *template* workflow:
- we fetch the alert (404 if missing),
- we copy optional alert context into the work order description/title,
- we DO NOT persist any alert linkage.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.models.alert import Alert
from app.models.work_order import WorkOrder
from app.repositories import alerts as alerts_repo
from app.repositories import work_orders as wo_repo
from app.schemas.work_orders import WorkOrderCreate, WorkOrderUpdate


def _now() -> datetime:
    """Return current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _ensure_work_order_number(db: Session, work_order: WorkOrder) -> None:
    """Ensure a WorkOrder instance has `work_order_number` computed.

    The repository list/get helpers typically set this derived attribute. Some
    tests or callers may return ORM objects without it; the API contract expects
    it, so we compute it on-demand when missing.
    """
    if getattr(work_order, "work_order_number", None) is not None:
        return

    from sqlalchemy import and_, func, or_, select

    work_order.work_order_number = db.execute(
        select(func.count())
        .select_from(WorkOrder)
        .where(
            or_(
                WorkOrder.created_at < work_order.created_at,
                and_(
                    WorkOrder.created_at == work_order.created_at,
                    WorkOrder.id <= work_order.id,
                ),
            )
        )
    ).scalar_one()


def _build_title_from_alert(alert: Alert) -> str:
    """Create a stable title when creating a work order from an alert."""
    equipment_hint = (
        f"equipment {alert.equipment_id}" if alert.equipment_id else "equipment n/a"
    )
    parameter_hint = (
        f"parameter {alert.parameter_id}" if alert.parameter_id else "parameter n/a"
    )
    return f"Alert follow-up: {equipment_hint} / {parameter_hint}"


def _build_description_from_alert(alert: Alert, payload: WorkOrderCreate) -> str:
    """Create a helpful description from an alert + payload.

    We preserve the user-provided payload description, and append alert context
    when present (issuer_name, current_value, suggested_action). We do not
    attempt to serialize jsonb context fields here; that belongs in an alerts API.
    """
    base = (payload.description or "").strip()
    pieces: list[str] = [base] if base else []
    if alert.issuer_name:
        pieces.append(f"Issuer: {alert.issuer_name}")
    if alert.current_value:
        pieces.append(f"Current value: {alert.current_value}")
    if alert.suggested_action:
        pieces.append(f"Suggested action: {alert.suggested_action}")
    return "\n".join(pieces)


# PUBLIC_INTERFACE
def create_work_order(db: Session, alert_id: str, payload: WorkOrderCreate) -> WorkOrder:
    """Create a work order using an alert as a *template*, not a persisted link.

    Args:
        db: Active database session.
        alert_id: UUID string of the source alert (used only for lookup/template).
        payload: Creation payload (legacy route shape).

    Returns:
        WorkOrder: Newly created work order.

    Raises:
        ProblemException: 404 alert_not_found if the alert does not exist.
    """
    alert = alerts_repo.get_alert(db, alert_id)
    if alert is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )

    # Live schema supports equipment_id on work_orders; if alert has it, reuse it.
    work_order = WorkOrder(
        equipment_id=alert.equipment_id,
        title=_build_title_from_alert(alert),
        description=_build_description_from_alert(alert, payload),
        priority=payload.priority.value,
        status="OPEN",
        assigned_to=None,
        closed_by=None,
    )
    wo_repo.add(db, work_order)
    db.commit()
    db.refresh(work_order)

    hydrated = wo_repo.get_by_id(db, work_order.id) or work_order
    _ensure_work_order_number(db, hydrated)
    return hydrated


# PUBLIC_INTERFACE
def get_work_order(db: Session, work_order_id: str) -> WorkOrder:
    """Return a work order by id or raise not-found.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.

    Returns:
        WorkOrder: The work order.

    Raises:
        ProblemException: 404 work_order_not_found if missing.
    """
    work_order = wo_repo.get_by_id(db, work_order_id)
    if work_order is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.WORK_ORDER_NOT_FOUND,
            detail=f"Work order '{work_order_id}' does not exist.",
        )
    _ensure_work_order_number(db, work_order)
    return work_order


# PUBLIC_INTERFACE
def update_work_order(db: Session, work_order_id: str, payload: WorkOrderUpdate) -> WorkOrder:
    """Update a work order within the constraints of the live schema.

    Supported updates are limited to columns that exist in `public.work_orders`:
    - title, description, priority, status, assigned_to, closed_by

    We do NOT implement legacy "close" lifecycle validations because the required
    schema fields do not exist in the live DB.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.
        payload: Partial update body (schema rejects no-op bodies).

    Returns:
        WorkOrder: The updated work order.

    Raises:
        ProblemException: 404 work_order_not_found if missing.
    """
    work_order = get_work_order(db, work_order_id)

    data = payload.model_dump(exclude_unset=True)

    if "title" in data and data["title"] is not None:
        work_order.title = data["title"]
    if "description" in data and data["description"] is not None:
        work_order.description = data["description"]
    if "priority" in data and payload.priority is not None:
        work_order.priority = payload.priority.value
    if "status" in data and payload.status is not None:
        work_order.status = payload.status.value
    if "assigned_to" in data:
        work_order.assigned_to = data["assigned_to"]
    if "closed_by" in data:
        work_order.closed_by = data["closed_by"]

    # Live schema keeps `updated_at` as a DB default; we do not manage it here.
    db.commit()
    db.refresh(work_order)

    hydrated = wo_repo.get_by_id(db, work_order.id) or work_order
    _ensure_work_order_number(db, hydrated)
    return hydrated


# PUBLIC_INTERFACE
def list_work_orders(
    db: Session,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    priority: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> tuple[list[WorkOrder], int]:
    """List work orders with filtering and pagination.

    Args:
        db: Active database session.
        page: 1-based page number.
        page_size: Number of items per page.
        status: Optional status filter (persisted uppercase text).
        priority: Optional priority filter (persisted uppercase text).
        created_from: Optional lower bound (inclusive) on created_at.
        created_to: Optional upper bound (inclusive) on created_at.

    Returns:
        tuple[list[WorkOrder], int]: Rows and total count.
    """
    rows, total = wo_repo.list_work_orders(
        db,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        created_from=created_from,
        created_to=created_to,
    )
    for row in rows:
        _ensure_work_order_number(db, row)
    return rows, total
