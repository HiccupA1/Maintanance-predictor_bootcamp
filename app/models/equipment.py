"""Equipment domain ORM models.

Reconciled to the live Supabase PostgreSQL schema (public.*):
- Primary keys and FK columns are UUID in the live DB.
- Some text fields have DB defaults (''), which we mirror at the ORM layer for
  consistency (without hard-coding server defaults).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class Equipment(Base):
    """A maintainable plant asset."""

    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    equipment_id: Mapped[str] = mapped_column(
        Text, unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # Live DB default is ''::text; keep Python default to avoid NULLs in ORM-side creation.
    location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criticality: Mapped[int] = mapped_column(nullable=False, default=1)
    last_service_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    parameters = relationship(
        "Parameter",
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by="Parameter.name",
    )


class Parameter(Base):
    """A thresholded measurement parameter for equipment."""

    __tablename__ = "parameters"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    equipment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False, default="")
    min_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    equipment = relationship("Equipment", back_populates="parameters")
    readings = relationship(
        "Reading",
        back_populates="parameter",
        cascade="all, delete-orphan",
        order_by="Reading.timestamp.desc()",
    )


class Reading(Base):
    """A recorded value for an equipment parameter."""

    __tablename__ = "readings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    equipment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    parameter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("parameters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        server_default="now()",
    )
    entered_by: Mapped[str] = mapped_column(
        Text, nullable=False, default="dev"
    )
    modified_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    modification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment = relationship("Equipment")
    parameter = relationship("Parameter", back_populates="readings")
