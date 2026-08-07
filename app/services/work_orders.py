"""Work order service layer aligned with the live Supabase schema."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.models.work_order import WorkOrder
from app.repositories import work_orders as wo_repo
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
    work_order = WorkOrder(
        equipment_id=payload.equipment_id,
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
    db: Session, work_order_id: str, payload: WorkOrderUpdate
) -> WorkOrder:
    """Update only live work-order columns."""
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

    db.commit()
    db.refresh(work_order)
    return wo_repo.get_by_id(db, work_order.id) or work_order


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
