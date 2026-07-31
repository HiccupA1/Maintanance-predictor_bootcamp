"""Alert ORM model for threshold breaches and work-order conversion."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType


def _uuid() -> str:
    """Return a UUID4 string."""
    return str(uuid4())


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class Alert(Base):
    """A parameter threshold breach and its maintenance lifecycle."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("equipment.id"), nullable=False, index=True
    )
    parameter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("parameters.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NEW", index=True
    )
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MEDIUM"
    )
    current_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    breach_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    min_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_priority: Mapped[str | None] = mapped_column(Text, nullable=True)
    issuer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    machine_details: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    readings_snapshot: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    equipment = relationship("Equipment")
    parameter = relationship("Parameter")
    work_order = relationship(
        "WorkOrder", back_populates="alert", uselist=False
    )

    @property
    def equipment_name(self) -> str | None:
        """Return the related equipment's human-readable name when available."""
        return self.equipment.name if self.equipment is not None else None

    @property
    def parameter_name(self) -> str | None:
        """Return the related parameter's human-readable name when available."""
        return self.parameter.name if self.parameter is not None else None
