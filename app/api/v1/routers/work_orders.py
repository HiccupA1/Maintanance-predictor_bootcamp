"""Work order API routes aligned with the live Supabase schema."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.errors import ErrorCode, ErrorItem, ProblemException, problem_responses
from app.db.session import get_db
from app.schemas.common import Priority, WorkOrderStatus
from app.schemas.work_orders import (
    WorkOrder,
    WorkOrderCreate,
    WorkOrderListResponse,
    WorkOrderSummary,
    WorkOrderUpdate,
)
from app.services import work_orders as service

router = APIRouter(tags=["work-orders"])


# PUBLIC_INTERFACE
@router.post(
    "/work-orders",
    response_model=WorkOrder,
    status_code=201,
    summary="Create a work order",
    responses=problem_responses(422),
)
def create_work_order(
    payload: WorkOrderCreate, db: Session = Depends(get_db)
) -> WorkOrder:
    """Create a work order."""
    return WorkOrder.model_validate(service.create_work_order(db, payload))


# PUBLIC_INTERFACE
@router.put(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
    summary="Update a work order",
    responses=problem_responses(404, 422),
)
def update_work_order(
    payload: WorkOrderUpdate,
    work_order_id: str = Path(..., description="UUID string of the work order."),
    db: Session = Depends(get_db),
) -> WorkOrder:
    """Update an existing work order."""
    return WorkOrder.model_validate(
        service.update_work_order(db, work_order_id, payload)
    )


# PUBLIC_INTERFACE
@router.delete(
    "/work-orders/{work_order_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a work order",
    dependencies=[Depends(require_roles(["PlantManager", "MaintenanceEngineer"]))],
)
def delete_work_order(
    work_order_id: str = Path(..., description="UUID string of the work order."),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a work order."""
    row = service.get_work_order(db, work_order_id)
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@router.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
    summary="Fetch a work order by id",
    responses=problem_responses(404),
)
def get_work_order(
    work_order_id: str = Path(..., description="UUID string of the work order."),
    db: Session = Depends(get_db),
) -> WorkOrder:
    """Return a single work order."""
    return WorkOrder.model_validate(service.get_work_order(db, work_order_id))


# PUBLIC_INTERFACE
@router.get(
    "/work-orders",
    response_model=WorkOrderListResponse,
    summary="List work orders",
    responses=problem_responses(422),
)
def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status_filter: WorkOrderStatus | None = Query(None, alias="status"),
    priority: Priority | None = Query(None),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> WorkOrderListResponse:
    """List work orders with filtering and pagination."""
    if (
        created_from is not None
        and created_to is not None
        and created_from > created_to
    ):
        raise ProblemException(
            status=422,
            code=ErrorCode.INVALID_REQUEST,
            detail="created_from must not be after created_to.",
            errors=[
                ErrorItem(
                    field="created_from",
                    message="created_from must be <= created_to.",
                    rule="range",
                )
            ],
        )

    rows, total = service.list_work_orders(
        db,
        page=page,
        page_size=page_size,
        status=status_filter.value if status_filter else None,
        priority=priority.value if priority else None,
        created_from=created_from,
        created_to=created_to,
    )
    return WorkOrderListResponse(
        items=[WorkOrderSummary.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
