"""Schemas for risk scores and the model registry (WP4)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.serialization import (
    coerce_uuid_to_str,
    normalize_datetime_to_utc,
    normalize_optional_datetime_to_utc,
)


class RiskScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    model_version_id: str
    model_version: str | None = None
    score: float = Field(..., ge=0, le=1)
    flagged: bool
    stage: str
    features: dict[str, float]
    scored_at: datetime

    @field_validator("id", "model_version_id", mode="before")
    @classmethod
    def _ids(cls, v: object) -> str:
        return coerce_uuid_to_str(v)

    @field_validator("scored_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> datetime:
        return normalize_datetime_to_utc(v)


class EquipmentRiskResponse(BaseModel):
    equipment_id: str
    asset_class: str | None
    status: str = Field(
        ...,
        description=(
            "scored | not_configured (no asset_class or model) | no_scores"
        ),
    )
    latest: RiskScoreResponse | None = None
    history: list[RiskScoreResponse] = []


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    kind: str
    asset_class: str
    stage: str
    threshold: float
    features: list[str]
    metrics: dict | None = None
    created_at: datetime
    stage_changed_at: datetime | None = None
    stage_changed_by: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _id(cls, v: object) -> str:
        return coerce_uuid_to_str(v)

    @field_validator("created_at", mode="before")
    @classmethod
    def _created(cls, v: object) -> datetime:
        return normalize_datetime_to_utc(v)

    @field_validator("stage_changed_at", mode="before")
    @classmethod
    def _changed(cls, v: object) -> datetime | None:
        return normalize_optional_datetime_to_utc(v)


class StageChange(BaseModel):
    stage: Literal["shadow", "active", "retired"]
