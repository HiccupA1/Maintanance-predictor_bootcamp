"""Work order repository (data access for work orders)."""

from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.work_order import WorkOrder


def _assign_work_order_number(db: Session, work_order: WorkOrder) -> WorkOrder:
    """Attach the stable 1-based creation-order number used for display."""
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
    return work_order


# PUBLIC_INTERFACE
def get_by_id(db: Session, work_order_id: str) -> WorkOrder | None:
    """Fetch a work order by id.

    Args:
        db: Active database session.
        work_order_id: UUID string of the work order.

    Returns:
        WorkOrder | None: The work order if found, otherwise ``None``.
    """
    work_order = db.execute(
        select(WorkOrder)
        .options(selectinload(WorkOrder.equipment))
        .where(WorkOrder.id == work_order_id)
    ).scalar_one_or_none()
    return _assign_work_order_number(db, work_order) if work_order else None


# NOTE:
# Live Supabase schema has no `work_orders.alert_id`, so repository functions
# must not expose alert-based lookups.


# PUBLIC_INTERFACE
def get_by_equipment(db: Session, equipment_id: str) -> list[WorkOrder]:
    """Fetch work orders for a given equipment id (UUID string).

    Live Supabase schema does not link work_orders to alerts, so equipment_id is
    the stable join key for UI flows.
    """
    return (
        db.execute(select(WorkOrder).where(WorkOrder.equipment_id == equipment_id))
        .scalars()
        .all()
    )


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

    numbered_work_orders = select(
        WorkOrder.id.label("id"),
        func.row_number()
        .over(order_by=(WorkOrder.created_at.asc(), WorkOrder.id.asc()))
        .label("work_order_number"),
    ).subquery()

    base = (
        select(WorkOrder, numbered_work_orders.c.work_order_number)
        .join(numbered_work_orders, numbered_work_orders.c.id == WorkOrder.id)
        .options(selectinload(WorkOrder.equipment))
    )
    count_stmt = select(func.count()).select_from(WorkOrder)
    for cond in conditions:
        base = base.where(cond)
        count_stmt = count_stmt.where(cond)

    total = db.execute(count_stmt).scalar_one()
    result_rows = (
        db.execute(
            base.order_by(WorkOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )
    rows = []
    for work_order, work_order_number in result_rows:
        work_order.work_order_number = work_order_number
        rows.append(work_order)
    return rows, total
