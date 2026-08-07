"""Work order repository (data access for live work orders)."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.work_order import WorkOrder


# PUBLIC_INTERFACE
def get_by_id(db: Session, work_order_id: str) -> WorkOrder | None:
    """Fetch a work order by UUID string."""
    return db.execute(
        select(WorkOrder).where(WorkOrder.id == work_order_id)
    ).scalar_one_or_none()


# PUBLIC_INTERFACE
def get_by_equipment(db: Session, equipment_id: str) -> list[WorkOrder]:
    """Fetch work orders associated with an equipment UUID."""
    return (
        db.execute(
            select(WorkOrder).where(WorkOrder.equipment_id == equipment_id)
        )
        .scalars()
        .all()
    )


# PUBLIC_INTERFACE
def add(db: Session, work_order: WorkOrder) -> WorkOrder:
    """Add a transient work order to the session without committing."""
    db.add(work_order)
    return work_order


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
    """List live work orders with filtering and pagination."""
    conditions = []
    if status is not None:
        conditions.append(WorkOrder.status == status)
    if priority is not None:
        conditions.append(WorkOrder.priority == priority)
    if created_from is not None:
        conditions.append(WorkOrder.created_at >= created_from)
    if created_to is not None:
        conditions.append(WorkOrder.created_at <= created_to)

    base = select(WorkOrder)
    count_stmt = select(func.count()).select_from(WorkOrder)
    for condition in conditions:
        base = base.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        base.order_by(WorkOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return rows, total
