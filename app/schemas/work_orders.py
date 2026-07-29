"""Pydantic schemas for Work Order endpoints.

Includes request schemas (create/update, part lines) and response schemas
(``WorkOrder``, ``WorkOrderSummary``, and the paginated list response). Field
names match the contract exactly (e.g., ``due_at``). The update schema enforces
the "no-op update rejected" rule.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import Priority, WorkOrderStatus


# PUBLIC_INTERFACE
class WorkOrderPartLineBase(BaseModel):
    """Base fields for a spare-part line."""

    part_name: str = Field(
        ..., min_length=1, description="Name or identifier of the spare part."
    )
    used: bool = Field(
        default=True, description="Whether the part was actually used."
    )
    notes: str | None = Field(
        default=None, description="Optional free-text notes for the part line."
    )


# PUBLIC_INTERFACE
class WorkOrderPartLineCreate(WorkOrderPartLineBase):
    """Payload for creating/replacing a spare-part line."""


# PUBLIC_INTERFACE
class WorkOrderPartLine(WorkOrderPartLineBase):
    """Spare-part line as returned in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique part-line id (UUID string).")


# PUBLIC_INTERFACE
class WorkOrderCreate(BaseModel):
    """Request body for creating a work order from an alert."""

    description: str = Field(
        ..., min_length=1, description="Description of the work to perform."
    )
    priority: Priority = Field(
        ..., description="Work order priority (CRITICAL, HIGH, MEDIUM)."
    )
    due_at: datetime | None = Field(
        default=None, description="Optional due timestamp (ISO 8601)."
    )
    parts: list[WorkOrderPartLineCreate] = Field(
        default_factory=list, description="Optional initial spare-part lines."
    )


# PUBLIC_INTERFACE
class WorkOrderUpdate(BaseModel):
    """Request body for updating a work order.

    All fields are optional, but at least one must be provided; an empty
    (no-op) update is rejected as ``invalid_request`` (422).
    """

    description: str | None = Field(default=None, min_length=1)
    priority: Priority | None = Field(default=None)
    status: WorkOrderStatus | None = Field(default=None)
    due_at: datetime | None = Field(default=None)
    resolution_notes: str | None = Field(default=None)
    root_cause: str | None = Field(default=None)
    closed_at: datetime | None = Field(default=None)
    parts: list[WorkOrderPartLineCreate] | None = Field(default=None)

    @model_validator(mode="after")
    def _reject_no_op(self) -> "WorkOrderUpdate":
        """Reject updates that carry no changes (no-op)."""
        if all(
            getattr(self, name) is None for name in self.__class__.model_fields
        ):
            raise ValueError(
                "At least one field must be provided; no-op update rejected."
            )
        return self


# PUBLIC_INTERFACE
class WorkOrder(BaseModel):
    """Full work order representation returned by detail/create/update."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_id: str
    equipment_id: str
    description: str
    priority: Priority
    status: WorkOrderStatus
    issuer_name: str | None = None
    due_at: datetime | None = None
    machine_details: dict | None = None
    readings_snapshot: dict | None = None
    resolution_notes: str | None = None
    root_cause: str | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    created_at: datetime
    updated_at: datetime
    parts: list[WorkOrderPartLine] = Field(default_factory=list)

    @field_validator("priority", "status", mode="before")
    @classmethod
    def _normalize_persisted_enum(cls, value: object) -> object:
        """Accept casing/whitespace drift while rejecting unknown values."""
        if isinstance(value, str):
            return value.strip().upper()
        return value


# PUBLIC_INTERFACE
class WorkOrderSummary(BaseModel):
    """Condensed work order representation used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_id: str
    equipment_id: str
    priority: Priority
    status: WorkOrderStatus
    due_at: datetime | None = None
    created_at: datetime

    @field_validator("priority", "status", mode="before")
    @classmethod
    def _normalize_persisted_enum(cls, value: object) -> object:
        """Accept casing/whitespace drift while rejecting unknown values."""
        if isinstance(value, str):
            return value.strip().upper()
        return value


# PUBLIC_INTERFACE
class WorkOrderListResponse(BaseModel):
    """Paginated list response for work orders."""

    items: list[WorkOrderSummary]
    total: int = Field(..., description="Total matching records.")
    page: int = Field(..., description="Current 1-based page number.")
    page_size: int = Field(..., description="Number of items per page.")
