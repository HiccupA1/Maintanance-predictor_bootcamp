"""Alert ORM model for threshold breaches and work-order conversion.

Reconciled to the live Supabase PostgreSQL schema (public.alerts).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SERVER_NOW, SERVER_UUID, Base, new_uuid

# Cross-dialect JSON type:
# - Supabase/Postgres: JSONB (matches live schema)
# - SQLite (tests): JSON (so CREATE TABLE works)
_JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Alert(Base):
    """A parameter threshold breach and its maintenance lifecycle."""

    __tablename__ = "alerts"

    __table_args__ = (Index("alerts_status_idx", "status"),)

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        server_default=SERVER_UUID,
    )
    equipment_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("equipment.id", ondelete="SET NULL"),
        nullable=True,
    )
    parameter_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("parameters.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="OPEN"
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="MEDIUM"
    )
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    breach_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    min_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_priority: Mapped[str | None] = mapped_column(Text, nullable=True)
    issuer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    machine_details: Mapped[dict | None] = mapped_column(
        _JSON_TYPE, nullable=True
    )
    readings_snapshot: Mapped[dict | None] = mapped_column(
        _JSON_TYPE, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=SERVER_NOW,
    )

    # Relationships are intentionally omitted here:
    # - Live schema snapshot does not require ORM relationship properties.
    # - Keeping ORM purely schema-faithful avoids “helper” properties that
    #   can accidentally reintroduce stale joins/expectations in service layers.
