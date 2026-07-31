"""WorkOrder ORM model.

Represents a work order created from an alert. The ``alert_id`` column is
unique to enforce the "one work order per alert" business rule at the database
level.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType


def _uuid() -> str:
    """Return a new UUID4 as a string."""
    return str(uuid4())


def _now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class WorkOrder(Base):
    """A work order derived from an alert."""

    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('CRITICAL', 'HIGH', 'MEDIUM')",
            name="ck_work_orders_priority",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED')",
            name="ck_work_orders_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid
    )
    # Unique => at most one work order per alert (enforced in DB).
    alert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("alerts.id"), unique=True, nullable=False
    )
    equipment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="OPEN"
    )
    issuer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    machine_details: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )
    readings_snapshot: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_by: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    alert = relationship("Alert", back_populates="work_order")
    equipment = relationship(
        "Equipment",
        primaryjoin="foreign(WorkOrder.equipment_id) == Equipment.id",
        viewonly=True,
    )
    parts = relationship(
        "WorkOrderPartLine",
        back_populates="work_order",
        cascade="all, delete-orphan",
        order_by="WorkOrderPartLine.id",
    )

    @property
    def equipment_name(self) -> str | None:
        """Return the linked equipment's human-readable name when available."""
        return self.equipment.name if self.equipment is not None else None
