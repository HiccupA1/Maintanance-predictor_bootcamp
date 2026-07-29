"""Work order service layer.

Holds all business rules for work orders, keeping HTTP concerns in the routers
and data access in the repositories. Enforces:

* alert existence (404 ``alert_not_found``),
* one work order per alert (409 ``duplicate_work_order``),
* single-transaction create with alert transition to ``IN_PROGRESS``,
* no updates to CLOSED work orders (409 ``invalid_state``),
* closure requirements for resolution notes, root cause, and parts,
* alert resolution and equipment service-date updates on close,
* not-found on fetch/update (404 ``work_order_not_found``).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.models.alert import Alert
from app.models.equipment import Equipment
from app.models.work_order import WorkOrder
from app.models.work_order_part_line import WorkOrderPartLine
from app.repositories import alerts as alerts_repo
from app.repositories import work_orders as wo_repo
from app.schemas.work_orders import WorkOrderCreate, WorkOrderUpdate

_ALERT_IN_PROGRESS = "IN_PROGRESS"


def _now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# PUBLIC_INTERFACE
def create_work_order(
    db: Session, alert_id: str, payload: WorkOrderCreate
) -> WorkOrder:
    """Create a work order from an alert in a single transaction.

    The alert must exist and must not already have a work order. On success the
    alert is transitioned to ``IN_PROGRESS`` and the whole change is committed
    atomically.
    """
    alert: Alert | None = alerts_repo.get_alert(db, alert_id)
    if alert is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )

    if wo_repo.get_by_alert(db, alert_id) is not None:
        raise ProblemException(
            status=409,
            code=ErrorCode.DUPLICATE_WORK_ORDER,
            detail=f"A work order already exists for alert '{alert_id}'.",
        )

    work_order = WorkOrder(
        alert_id=alert.id,
        equipment_id=alert.equipment_id,
        description=payload.description,
        priority=payload.priority.value,
        status="OPEN",
        issuer_name=alert.issuer_name,
        due_at=payload.due_at,
        machine_details=alert.machine_details,
        readings_snapshot=alert.readings_snapshot,
    )
    for part in payload.parts:
        work_order.parts.append(
            WorkOrderPartLine(
                part_name=part.part_name, used=part.used, notes=part.notes
            )
        )

    wo_repo.add(db, work_order)
    alert.status = _ALERT_IN_PROGRESS

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ProblemException(
            status=409,
            code=ErrorCode.DUPLICATE_WORK_ORDER,
            detail=f"A work order already exists for alert '{alert_id}'.",
        ) from None
    db.refresh(work_order)
    return work_order


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
    db: Session, work_order_id: str, payload: WorkOrderUpdate
) -> WorkOrder:
    """Apply a partial update and enforce the close lifecycle contract."""
    work_order = get_work_order(db, work_order_id)

    if work_order.status == "CLOSED":
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_STATE,
            detail="A closed work order cannot be modified.",
        )

    data = payload.model_dump(exclude_unset=True)

    if "description" in data and data["description"] is not None:
        work_order.description = data["description"]
    if "priority" in data and data["priority"] is not None:
        work_order.priority = payload.priority.value
    if "due_at" in data:
        work_order.due_at = data["due_at"]
    if "resolution_notes" in data:
        work_order.resolution_notes = data["resolution_notes"]
    if "root_cause" in data:
        work_order.root_cause = data["root_cause"]
    if "closed_at" in data:
        work_order.closed_at = data["closed_at"]

    if "parts" in data and payload.parts is not None:
        work_order.parts.clear()
        for part in payload.parts:
            work_order.parts.append(
                WorkOrderPartLine(
                    part_name=part.part_name, used=part.used, notes=part.notes
                )
            )

    if "status" in data and data["status"] is not None:
        new_status = payload.status.value
        if new_status == "CLOSED":
            if not work_order.resolution_notes or not work_order.root_cause:
                raise ProblemException(
                    status=422,
                    code=ErrorCode.INVALID_REQUEST,
                    detail="Closing requires resolution_notes and root_cause.",
                )
            if not work_order.parts:
                raise ProblemException(
                    status=422,
                    code=ErrorCode.INVALID_REQUEST,
                    detail=(
                        "Closing requires at least one part line; use N/A "
                        "when no part was used."
                    ),
                )

        work_order.status = new_status
        if new_status == "CLOSED":
            work_order.closed_at = work_order.closed_at or _now()
            work_order.closed_by = "dev"
            alert = db.get(Alert, work_order.alert_id)
            if alert is not None:
                alert.status = "RESOLVED"
            equipment = db.get(Equipment, work_order.equipment_id)
            if equipment is not None:
                equipment.last_service_date = work_order.closed_at
        else:
            work_order.closed_at = None
            work_order.closed_by = None

    db.commit()
    db.refresh(work_order)
    return work_order
