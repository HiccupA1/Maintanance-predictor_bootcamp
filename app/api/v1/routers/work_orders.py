"""Work order API routes (HTTP layer only).

Wires work order contract endpoints to the service layer, handling only HTTP
concerns: path/verb, request/response models, dependency injection, and
query-parameter validation (including timestamp from/to ordering).

Important schema note (live Supabase):
- public.work_orders has NO alert_id column (alerts and work_orders are not FK-linked).
- The legacy "create from alert" route remains for UX continuity, but it treats the
  alert as a *template* only (no persisted linkage, no alert status mutation).
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

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
    "/alerts/{alert_id}/work-orders",
    response_model=WorkOrder,
    status_code=201,
    summary="Create a work order from an alert (template workflow)",
    description=(
        "Legacy UX path: creates a work order using the alert as a template. "
        "The created work order is NOT linked to the alert in the database "
        "(live Supabase schema has no work_orders.alert_id)."
    ),
    responses=problem_responses(404, 422),
)
def create_work_order(
    payload: WorkOrderCreate,
    alert_id: str = Path(..., description="UUID string of the source alert."),
    db: Session = Depends(get_db),  # noqa: B008
) -> WorkOrder:
    """Create a work order from an alert (template-only workflow).

    Args:
        payload: Validated creation body.
        alert_id: UUID string of the source alert (lookup/template only).
        db: Injected database session.

    Returns:
        WorkOrder: The created work order (HTTP 201).
    """
    row = service.create_work_order(db, alert_id, payload)
    return WorkOrder.model_validate(row)


# PUBLIC_INTERFACE
@router.put(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
    summary="Update a work order",
    description=(
        "Applies a partial update. Empty (no-op) bodies are rejected as "
        "invalid_request (422)."
    ),
    responses=problem_responses(404, 422),
)
def update_work_order(
    payload: WorkOrderUpdate,
    work_order_id: str = Path(..., description="UUID string of the work order."),
    db: Session = Depends(get_db),  # noqa: B008
) -> WorkOrder:
    """Update an existing work order.

    Args:
        payload: Validated update body (guaranteed non-empty by the schema).
        work_order_id: UUID string of the work order.
        db: Injected database session.

    Returns:
        WorkOrder: The updated work order.
    """
    row = service.update_work_order(db, work_order_id, payload)
    return WorkOrder.model_validate(row)


# PUBLIC_INTERFACE
@router.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
    summary="Fetch a work order by id",
    responses=problem_responses(404),
)
def get_work_order(
    work_order_id: str = Path(..., description="UUID string of the work order."),
    db: Session = Depends(get_db),  # noqa: B008
) -> WorkOrder:
    """Return a single work order by id.

    Args:
        work_order_id: UUID string of the work order.
        db: Injected database session.

    Returns:
        WorkOrder: The requested work order.
    """
    row = service.get_work_order(db, work_order_id)
    return WorkOrder.model_validate(row)


# PUBLIC_INTERFACE
@router.get(
    "/work-orders",
    response_model=WorkOrderListResponse,
    summary="List work orders",
    description=(
        "Lists work orders with pagination and optional filters. Supports "
        "status/priority filters and a created_from/created_to time window; "
        "created_from must not be after created_to."
    ),
    responses=problem_responses(422),
)
def list_work_orders(
    page: int = Query(1, ge=1, description="1-based page number."),  # noqa: B008
    page_size: int = Query(  # noqa: B008
        20, ge=1, le=200, description="Items per page (1-200)."
    ),
    status_filter: WorkOrderStatus | None = Query(  # noqa: B008
        None, alias="status", description="Filter by work order status."
    ),
    priority: Priority | None = Query(  # noqa: B008
        None, description="Filter by work order priority."
    ),
    created_from: datetime | None = Query(  # noqa: B008
        None, description="Inclusive lower bound for created_at (ISO 8601)."
    ),
    created_to: datetime | None = Query(  # noqa: B008
        None, description="Inclusive upper bound for created_at (ISO 8601)."
    ),
    db: Session = Depends(get_db),  # noqa: B008
) -> WorkOrderListResponse:
    """List work orders with filtering and pagination.

    Args:
        page: 1-based page number (>= 1).
        page_size: Items per page (1-200).
        status_filter: Optional status filter.
        priority: Optional priority filter.
        created_from: Optional inclusive lower time bound.
        created_to: Optional inclusive upper time bound.
        db: Injected database session.

    Returns:
        WorkOrderListResponse: The paginated result set.

    Raises:
        ProblemException: ``invalid_request`` (422) when created_from is after
            created_to.
    """
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
        items=[WorkOrderSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
