"""Equipment domain ORM models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    """Return a UUID4 string."""
    return str(uuid4())


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class Equipment(Base):
    """A maintainable plant asset."""

    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    criticality: Mapped[int] = mapped_column(nullable=False)
    last_service_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("equipment.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    min_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("equipment.id"), index=True, nullable=False
    )
    parameter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parameters.id"), index=True, nullable=False
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True, nullable=False
    )
    entered_by: Mapped[str] = mapped_column(
        String(255), nullable=False, default="dev"
    )
    modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    modification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment = relationship("Equipment")
    parameter = relationship("Parameter", back_populates="readings")
