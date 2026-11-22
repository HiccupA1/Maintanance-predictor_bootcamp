"""Model registry and risk score ORM models (WP4, ADR-0007)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Text,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SERVER_NOW, SERVER_UUID, Base, new_uuid

_JSON = JSON().with_variant(JSONB, "postgresql")

STAGES = ("shadow", "active", "retired")


class ModelVersion(Base):
    """A registered model artifact and its rollout stage."""

    __tablename__ = "model_versions"
    __table_args__ = (
        CheckConstraint(
            "stage in ('shadow', 'active', 'retired')",
            name="model_versions_stage_check",
        ),
        CheckConstraint(
            "kind in ('failure_risk', 'anomaly')",
            name="model_versions_kind_check",
        ),
        Index(
            "model_versions_one_active",
            "kind",
            "asset_class",
            unique=True,
            postgresql_where=text("stage = 'active'"),
            sqlite_where=text("stage = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        server_default=SERVER_UUID,
    )
    version: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="failure_risk"
    )
    asset_class: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="shadow"
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    features: Mapped[list] = mapped_column(_JSON, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=SERVER_NOW
    )
    stage_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stage_changed_by: Mapped[str | None] = mapped_column(Text, nullable=True)


class RiskScore(Base):
    """One model score for one piece of equipment at one time."""

    __tablename__ = "risk_scores"
    __table_args__ = (
        Index(
            "risk_scores_equipment_scored_idx",
            "equipment_id",
            text("scored_at desc"),
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        server_default=SERVER_UUID,
    )
    equipment_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_version_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("model_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[dict] = mapped_column(_JSON, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=SERVER_NOW
    )
