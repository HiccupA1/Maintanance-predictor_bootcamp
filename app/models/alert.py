"""Alert ORM model for threshold breaches and work-order conversion.

Reconciled to the live Supabase PostgreSQL schema (public.alerts).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    """A parameter threshold breach and its maintenance lifecycle."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    # Live schema: equipment_id is nullable and ON DELETE SET NULL.
    equipment_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("equipment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parameter_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("parameters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="'OPEN'::text", index=True
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="'MEDIUM'::text"
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
    machine_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    readings_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    equipment = relationship("Equipment")
    parameter = relationship("Parameter")

    @property
    def equipment_name(self) -> str | None:
        """Return the related equipment's human-readable name when available."""
        return self.equipment.name if self.equipment is not None else None

    @property
    def parameter_name(self) -> str | None:
        """Return the related parameter's human-readable name when available."""
        return self.parameter.name if self.parameter is not None else None
