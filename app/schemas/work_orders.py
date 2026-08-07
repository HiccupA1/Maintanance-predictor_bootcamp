"""Pydantic schemas for Work Order endpoints (aligned to live Supabase schema).

Live public.work_orders columns:
- id (uuid)
- equipment_id (uuid nullable)
- title (text not null)
- description (text nullable)
- status (text not null, default OPEN)
- priority (text not null, default MEDIUM)
- assigned_to (text nullable)
- closed_by (text nullable)
- created_at/updated_at (timestamptz default now)

Note: The API routes still include a legacy "create from alert" path. That route
accepts a description/priority payload, but the persisted model is the live
work_orders shape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import Priority, WorkOrderStatus
from app.schemas.serialization import (
    coerce_optional_uuid_to_str,
    coerce_uuid_to_str,
    normalize_optional_datetime_to_utc,
)


# PUBLIC_INTERFACE
class WorkOrderCreate(BaseModel):
    """Request body for creating a work order (persisted to public.work_orders).

    Note: A legacy router may still accept an `{alert_id}` path parameter, but
    the work order itself is NOT linked to alerts in the live schema.
    """

    title: str = Field(..., min_length=1, description="Short work order title.")
    equipment_id: str | None = Field(
        default=None,
        description="Optional equipment UUID string to associate the work order.",
    )
    description: str | None = Field(
        default=None, description="Optional description of the work to perform."
    )
    priority: Priority = Field(
        ..., description="Work order priority (CRITICAL, HIGH, MEDIUM)."
    )


# PUBLIC_INTERFACE
class WorkOrderUpdate(BaseModel):
    """Request body for updating a work order."""

    title: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    priority: Priority | None = Field(default=None)
    status: WorkOrderStatus | None = Field(default=None)
    assigned_to: str | None = Field(default=None, min_length=1)
    closed_by: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _reject_no_op(self) -> "WorkOrderUpdate":
        """Reject updates that carry no changes (no-op)."""
        if all(getattr(self, name) is None for name in self.__class__.model_fields):
            raise ValueError("At least one field must be provided; no-op update rejected.")
        return self


# PUBLIC_INTERFACE
class WorkOrder(BaseModel):
    """Full work order representation returned by detail/create/update."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    equipment_id: str | None = None
    title: str
    description: str | None = None
    priority: Priority
    status: WorkOrderStatus
    assigned_to: str | None = None
    closed_by: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id_to_str(cls, v: object) -> str:
        """Coerce UUID-like identifiers into string form."""
        return coerce_uuid_to_str(v)

    @field_validator("equipment_id", mode="before")
    @classmethod
    def _coerce_optional_equipment_id_to_str(cls, v: object) -> str | None:
        """Coerce optional UUID-like identifiers into string form."""
        return coerce_optional_uuid_to_str(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamps_to_utc(cls, v: object) -> datetime | None:
        """Normalize tz-naive datetimes to UTC-aware values (preserve None)."""
        return normalize_optional_datetime_to_utc(v)

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
    equipment_id: str | None = None
    title: str
    priority: Priority
    status: WorkOrderStatus
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id_to_str(cls, v: object) -> str:
        """Coerce UUID-like identifiers into string form."""
        return coerce_uuid_to_str(v)

    @field_validator("equipment_id", mode="before")
    @classmethod
    def _coerce_optional_equipment_id_to_str(cls, v: object) -> str | None:
        """Coerce optional UUID-like identifiers into string form."""
        return coerce_optional_uuid_to_str(v)

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_created_at_to_utc(cls, v: object) -> datetime | None:
        """Normalize tz-naive datetimes to UTC-aware values (preserve None)."""
        return normalize_optional_datetime_to_utc(v)

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
