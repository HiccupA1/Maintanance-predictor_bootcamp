"""Pydantic schemas for equipment, parameter, reading, and alert APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DomainBase(BaseModel):
    """Base response configuration for ORM-backed domain schemas."""

    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class MeResponse(BaseModel):
    """Current development identity returned by the RBAC shim."""

    user_id: str = Field(..., description="Development user identifier.")
    name: str = Field(..., description="Display name for the development user.")
    role: str = Field(..., description="Development role used for UI gating.")

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_user_id_to_str(cls, v: object) -> str:
        """Coerce UUID-like identifiers into string form.

        The API contract exposes `user_id` as a string, but the persistence layer
        may supply UUID values (e.g., from SQLAlchemy/DB UUID columns).
        """
        if isinstance(v, UUID):
            return str(v)
        return v  # type: ignore[return-value]


# PUBLIC_INTERFACE
class EquipmentCreate(BaseModel):
    """Payload for creating equipment."""

    equipment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    criticality: int = Field(..., ge=1, le=5)


# PUBLIC_INTERFACE
class EquipmentUpdate(EquipmentCreate):
    """Payload for replacing equipment metadata."""


# PUBLIC_INTERFACE
class EquipmentResponse(DomainBase):
    """Equipment response."""

    id: str
    equipment_id: str
    name: str
    location: str
    type: str
    criticality: int
    last_service_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def coerce_timestamps_to_utc(cls, v: object) -> datetime:
        """Coerce persisted timestamps to UTC-aware datetimes.

        Some DB backends/drivers may return timezone-naive values even when the
        column is declared with timezone support. The API contract expects
        proper datetimes; we normalize naive values to UTC to satisfy the
        response schema consistently.
        """
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v  # type: ignore[return-value]


# PUBLIC_INTERFACE
class EquipmentListResponse(BaseModel):
    """Equipment collection response."""

    items: list[EquipmentResponse]
    total: int


# PUBLIC_INTERFACE
class ParameterCreate(BaseModel):
    """Payload for creating a threshold parameter."""

    name: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    min_threshold: float | None = None
    max_threshold: float | None = None
    active: bool = True
    suggested_action: str | None = None

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ParameterCreate":
        """Require at least one threshold and a coherent range."""
        if self.min_threshold is None and self.max_threshold is None:
            raise ValueError("At least one of min_threshold or max_threshold is required.")
        if (
            self.min_threshold is not None
            and self.max_threshold is not None
            and self.min_threshold > self.max_threshold
        ):
            raise ValueError("min_threshold must not exceed max_threshold.")
        return self


# PUBLIC_INTERFACE
class ParameterUpdate(ParameterCreate):
    """Payload for replacing a parameter threshold configuration."""


# PUBLIC_INTERFACE
class ParameterResponse(DomainBase):
    """Parameter response."""

    id: str
    equipment_id: str
    name: str
    unit: str
    min_threshold: float | None = None
    max_threshold: float | None = None
    active: bool
    suggested_action: str | None = None
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class ReadingCreate(BaseModel):
    """Payload for recording a string-valued reading."""

    equipment_id: str = Field(..., min_length=1)
    parameter_id: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    timestamp: datetime | None = None


# PUBLIC_INTERFACE
class ReadingUpdate(BaseModel):
    """Payload for editing a reading value."""

    value: str = Field(..., min_length=1)
    modification_reason: str = Field(..., min_length=1)


# PUBLIC_INTERFACE
class ReadingResponse(DomainBase):
    """Reading response including audit fields."""

    id: str
    equipment_id: str
    parameter_id: str
    value: str
    timestamp: datetime
    entered_by: str
    modified_by: str | None = None
    modified_at: datetime | None = None
    modification_reason: str | None = None


# PUBLIC_INTERFACE
class AlertResponse(DomainBase):
    """Threshold breach alert response."""

    id: str
    equipment_id: str
    equipment_name: str | None = None
    parameter_id: str | None = None
    parameter_name: str | None = None
    status: str
    priority: str
    current_value: str | None = None
    breach_timestamp: datetime | None = None
    min_threshold: float | None = None
    max_threshold: float | None = None
    suggested_action: str | None = None
    why_priority: str | None = None
    created_at: datetime
    updated_at: datetime
