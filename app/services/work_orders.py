"""Work order service layer aligned with the live Supabase schema."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ErrorItem, ProblemException
from app.models.alert import Alert
from app.models.equipment import Equipment
from app.models.work_order import WorkOrder
from app.repositories import work_orders as wo_repo
from app.schemas.common import WorkOrderStatus
from app.schemas.work_orders import WorkOrderCreate, WorkOrderUpdate


# PUBLIC_INTERFACE
def create_work_order(db: Session, payload: WorkOrderCreate) -> WorkOrder:
    """Create a work order from live request fields.

    Args:
        db: Active database session.
        payload: Validated work-order creation payload.

    Returns:
        WorkOrder: The persisted work order.
    """
    equipment_id = payload.equipment_id
    if payload.alert_id is not None:
        alert = db.get(Alert, payload.alert_id)
        if alert is None:
            raise ProblemException(
                status=404,
                code=ErrorCode.ALERT_NOT_FOUND,
                detail=f"Alert '{payload.alert_id}' does not exist.",
            )
        if db.execute(
            select(WorkOrder.id).where(WorkOrder.alert_id == alert.id)
        ).first():
            raise ProblemException(
                status=409,
                code=ErrorCode.INVALID_STATE,
                detail="A work order already exists for this alert (FR7).",
            )
        equipment_id = equipment_id or alert.equipment_id

    work_order = WorkOrder(
        equipment_id=equipment_id,
        alert_id=payload.alert_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status="OPEN",
        assigned_to=None,
        closed_by=None,
    )
    wo_repo.add(db, work_order)
    db.commit()
    db.refresh(work_order)
    return wo_repo.get_by_id(db, work_order.id) or work_order


# PUBLIC_INTERFACE
def get_work_order(db: Session, work_order_id: str) -> WorkOrder:
    """Return a work order by id or raise a not-found problem."""
    work_order = wo_repo.get_by_id(db, work_order_id)
    if work_order is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.WORK_ORDER_NOT_FOUND,
            detail=f"Work order '{work_order_id}' does not exist.",
        )
    return work_order


# PUBLIC_INTERFACE
def update_work_order(
    db: Session,
    work_order_id: str,
    payload: WorkOrderUpdate,
    actor: str | None = None,
) -> WorkOrder:
    """Update a work order; a transition to CLOSED is a closure (FR9-FR10)."""
    work_order = get_work_order(db, work_order_id)
    data = payload.model_dump(exclude_unset=True)

    if work_order.status == "CLOSED" and data:
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_STATE,
            detail="Closed work orders cannot be modified.",
        )

    closing = payload.status == WorkOrderStatus.CLOSED
    if closing:
        _close(db, work_order, payload, actor)
        data.pop("status", None)
    elif any(
        data.get(name) is not None
        for name in ("failure_confirmed", "failure_mode")
    ):
        raise _invalid(
            "failure_confirmed",
            "Failure labels are recorded when the work order is closed.",
        )

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
    if "closed_by" in data and not closing:
        work_order.closed_by = data["closed_by"]

    db.commit()
    db.refresh(work_order)
    return wo_repo.get_by_id(db, work_order.id) or work_order


def _invalid(field: str, message: str) -> ProblemException:
    return ProblemException(
        status=422,
        code=ErrorCode.INVALID_REQUEST,
        detail=message,
        errors=[ErrorItem(field=field, message=message, rule="closure")],
    )


def _close(
    db: Session,
    work_order: WorkOrder,
    payload: WorkOrderUpdate,
    actor: str | None,
) -> None:
    """Apply FR9 closure rules and FR10 side effects."""
    for field in ("resolution_notes", "root_cause"):
        if getattr(payload, field) is None:
            raise _invalid(field, f"{field} is required to close.")
    if payload.failure_confirmed is None:
        raise _invalid(
            "failure_confirmed",
            "failure_confirmed is required to close (was this a failure?).",
        )
    if payload.failure_confirmed and payload.failure_mode is None:
        raise _invalid(
            "failure_mode", "failure_mode is required for a confirmed failure."
        )
    if not payload.failure_confirmed and payload.failure_mode is not None:
        raise _invalid(
            "failure_mode", "failure_mode applies only to confirmed failures."
        )

    now = datetime.now(timezone.utc)
    work_order.status = WorkOrderStatus.CLOSED.value
    work_order.resolution_notes = payload.resolution_notes
    work_order.root_cause = payload.root_cause
    work_order.failure_confirmed = payload.failure_confirmed
    work_order.failure_mode = (
        payload.failure_mode.value if payload.failure_mode else None
    )
    work_order.closed_at = now
    work_order.closed_by = actor or payload.closed_by

    # FR10: resolve the source alert and record the service date.
    if work_order.alert_id is not None:
        alert = db.get(Alert, work_order.alert_id)
        if alert is not None:
            alert.status = "RESOLVED"
    if work_order.equipment_id is not None:
        equipment = db.get(Equipment, work_order.equipment_id)
        if equipment is not None:
            equipment.last_service_date = now


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
    """List work orders with filtering and pagination."""
    return wo_repo.list_work_orders(
        db,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        created_from=created_from,
        created_to=created_to,
    )
