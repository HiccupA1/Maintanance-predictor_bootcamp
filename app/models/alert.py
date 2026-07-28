"""Alert ORM model (MVP stub).

This is a deliberately minimal representation of an Alert, provided only to
support the Work Order flow required by the contract:

* alert existence check during work order creation, and
* transition of the alert status to ``IN_PROGRESS`` when a work order is
  created.

It is clearly marked as an MVP stub and is not the full Alert schema.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType


def _uuid() -> str:
    """Return a new UUID4 as a string."""
    return str(uuid4())


def _now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Alert(Base):
    """Minimal alert record (MVP stub) supporting the work order flow."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid
    )
    equipment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # Minimal lifecycle set needed for this flow.
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NEW"
    )
    issuer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Snapshots used to populate work order context on creation.
    machine_details: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )
    readings_snapshot: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    work_order = relationship(
        "WorkOrder", back_populates="alert", uselist=False
    )
