"""Work order repository (data access for work orders)."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.work_order import WorkOrder


# PUBLIC_INTERFACE
def get_by_id(db: Session, work_order_id: str) -> WorkOrder | None:
    """Fetch a work order by id.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.

    Returns:
        WorkOrder | None: The work order if found, otherwise ``None``.
    """
    return db.execute(
        select(WorkOrder).where(WorkOrder.id == work_order_id)
    ).scalar_one_or_none()


# PUBLIC_INTERFACE
def get_by_alert(db: Session, alert_id: str) -> WorkOrder | None:
    """Fetch the work order for a given alert, if any.

    Args:
        db: Active database session.
        alert_id: UUID string of the alert.

    Returns:
        WorkOrder | None: The linked work order, or ``None``.
    """
    return db.execute(
        select(WorkOrder).where(WorkOrder.alert_id == alert_id)
    ).scalar_one_or_none()


# PUBLIC_INTERFACE
def add(db: Session, work_order: WorkOrder) -> WorkOrder:
    """Add a new work order to the session (no commit).

    Args:
        db: Active database session.
        work_order: The transient work order to persist.

    Returns:
        WorkOrder: The same instance, now added to the session.
    """
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
    """List work orders with filtering and pagination.

    Args:
        db: Active database session.
        page: 1-based page number.
        page_size: Number of items per page.
        status: Optional status filter.
        priority: Optional priority filter.
        created_from: Optional lower bound (inclusive) on ``created_at``.
        created_to: Optional upper bound (inclusive) on ``created_at``.

    Returns:
        tuple[list[WorkOrder], int]: The page of results and the total count.
    """
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
    for cond in conditions:
        base = base.where(cond)
        count_stmt = count_stmt.where(cond)

    total = db.execute(count_stmt).scalar_one()
    rows = (
        db.execute(
            base.order_by(WorkOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return list(rows), total
