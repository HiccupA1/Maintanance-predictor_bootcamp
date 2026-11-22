"""Pydantic schemas for live public.work_orders endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import FailureMode, Priority, WorkOrderStatus
from app.schemas.serialization import (
    coerce_optional_uuid_to_str,
    coerce_uuid_to_str,
    normalize_optional_datetime_to_utc,
)


# PUBLIC_INTERFACE
class WorkOrderCreate(BaseModel):
    """Request body for creating a live work order."""

    title: str = Field(
        ..., min_length=1, description="Short work-order title."
    )
    equipment_id: str | None = Field(
        default=None,
        description="Optional equipment UUID.",
    )
    description: str | None = Field(
        default=None,
        description="Optional work-order description.",
    )
    priority: Priority = Field(
        ...,
        description="Work-order priority.",
    )
    alert_id: str | None = Field(
        default=None,
        description="Source alert (FR7). At most one work order per alert.",
    )


# PUBLIC_INTERFACE
class WorkOrderUpdate(BaseModel):
    """Request body for updating a live work order.

    Setting ``status`` to CLOSED is a closure (FR9) and additionally requires
    ``resolution_notes``, ``root_cause`` and ``failure_confirmed``, plus
    ``failure_mode`` when a failure is confirmed.
    """

    title: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    priority: Priority | None = None
    status: WorkOrderStatus | None = None
    assigned_to: str | None = Field(default=None, min_length=1)
    closed_by: str | None = Field(default=None, min_length=1)
    resolution_notes: str | None = Field(default=None, min_length=1)
    root_cause: str | None = Field(default=None, min_length=1)
    failure_confirmed: bool | None = None
    failure_mode: FailureMode | None = None

    @model_validator(mode="after")
    def _reject_no_op(self) -> "WorkOrderUpdate":
        """Reject an update with no supplied fields."""
        if all(
            getattr(self, name) is None for name in self.__class__.model_fields
        ):
            raise ValueError(
                "At least one field must be provided; no-op update rejected."
            )
        return self


# PUBLIC_INTERFACE
class WorkOrder(BaseModel):
    """Full work-order response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    equipment_id: str | None = None
    alert_id: str | None = None
    title: str
    description: str | None = None
    # Responses accept any stored value (D4): one legacy row must not turn a
    # whole list page into a 500. Requests are still validated strictly.
    priority: Annotated[Priority | str, Field(union_mode="left_to_right")]
    status: Annotated[WorkOrderStatus | str, Field(union_mode="left_to_right")]
    assigned_to: str | None = None
    closed_by: str | None = None
    resolution_notes: str | None = None
    root_cause: str | None = None
    closed_at: datetime | None = None
    failure_confirmed: bool | None = None
    failure_mode: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("alert_id", mode="before")
    @classmethod
    def _coerce_alert_id(cls, value: object) -> str | None:
        """Coerce optional alert UUID identifiers to strings."""
        return coerce_optional_uuid_to_str(value)

    @field_validator("closed_at", mode="before")
    @classmethod
    def _coerce_closed_at(cls, value: object) -> datetime | None:
        """Normalize the closure timestamp to UTC."""
        return normalize_optional_datetime_to_utc(value)

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: object) -> str:
        """Coerce UUID identifiers to strings."""
        return coerce_uuid_to_str(value)

    @field_validator("equipment_id", mode="before")
    @classmethod
    def _coerce_equipment_id(cls, value: object) -> str | None:
        """Coerce optional equipment UUID identifiers to strings."""
        return coerce_optional_uuid_to_str(value)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamps(cls, value: object) -> datetime | None:
        """Normalize database timestamps to UTC-aware values."""
        return normalize_optional_datetime_to_utc(value)

    @field_validator("priority", "status", mode="before")
    @classmethod
    def _normalize_enums(cls, value: object) -> object:
        """Normalize persisted text enum values."""
        return value.strip().upper() if isinstance(value, str) else value


# PUBLIC_INTERFACE
class WorkOrderSummary(BaseModel):
    """Condensed work-order response for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    equipment_id: str | None = None
    title: str
    # Tolerant of legacy stored values (D4); enum first.
    priority: Annotated[Priority | str, Field(union_mode="left_to_right")]
    status: Annotated[WorkOrderStatus | str, Field(union_mode="left_to_right")]
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: object) -> str:
        """Coerce UUID identifiers to strings."""
        return coerce_uuid_to_str(value)

    @field_validator("equipment_id", mode="before")
    @classmethod
    def _coerce_equipment_id(cls, value: object) -> str | None:
        """Coerce optional equipment UUID identifiers to strings."""
        return coerce_optional_uuid_to_str(value)

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_created_at(cls, value: object) -> datetime | None:
        """Normalize the creation timestamp to UTC."""
        return normalize_optional_datetime_to_utc(value)

    @field_validator("priority", "status", mode="before")
    @classmethod
    def _normalize_enums(cls, value: object) -> object:
        """Normalize persisted text enum values."""
        return value.strip().upper() if isinstance(value, str) else value


# PUBLIC_INTERFACE
class WorkOrderListResponse(BaseModel):
    """Paginated work-order list response."""

    items: list[WorkOrderSummary]
    total: int = Field(..., description="Total matching records.")
    page: int = Field(..., description="Current page.")
    page_size: int = Field(..., description="Items per page.")
