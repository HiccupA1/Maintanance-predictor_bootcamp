"""Work order service layer.

Holds all business rules for work orders, keeping HTTP concerns in the routers
and data access in the repositories. Enforces:

* alert existence (404 ``alert_not_found``),
* one work order per alert (409 ``duplicate_work_order``),
* single-transaction create with alert transition to ``IN_PROGRESS``,
* no updates to CLOSED work orders (409 ``invalid_state``),
* not-found on fetch/update (404 ``work_order_not_found``).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.models.alert import Alert
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

    Args:
        db: Active database session.
        alert_id: UUID string of the source alert.
        payload: Validated creation payload.

    Returns:
        WorkOrder: The newly created work order.

    Raises:
        ProblemException: ``alert_not_found`` (404) or ``duplicate_work_order``
            (409).
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
    # Alert lifecycle transition happens within the same transaction.
    alert.status = _ALERT_IN_PROGRESS

    try:
        db.commit()
    except IntegrityError:
        # Guard against a race on the unique alert_id constraint.
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
    """Return a work order by id or raise a not-found problem.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.

    Returns:
        WorkOrder: The work order.

    Raises:
        ProblemException: ``work_order_not_found`` (404).
    """
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
    """Apply a partial update to a work order.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.
        payload: Validated update payload (already guaranteed non-empty).

    Returns:
        WorkOrder: The updated work order.

    Raises:
        ProblemException: ``work_order_not_found`` (404) or ``invalid_state``
            (409) when the work order is already CLOSED.
    """
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
        work_order.status = new_status
        work_order.closed_at = _now() if new_status == "CLOSED" else None

    db.commit()
    db.refresh(work_order)
    return work_order
