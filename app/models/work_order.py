"""WorkOrder ORM model.

Reconciled to the live Supabase PostgreSQL schema (public.work_orders):
- No alert_id column exists in live DB (alerts and work_orders are not FK-linked).
- work_orders has title (required), description (nullable), assigned_to, closed_by.
- equipment_id is nullable UUID with ON DELETE SET NULL.
- status/priority are TEXT defaults 'OPEN'/'MEDIUM'.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SERVER_NOW, SERVER_UUID, Base, new_uuid


class WorkOrder(Base):
    """A work order representing a maintenance task."""

    __tablename__ = "work_orders"

    __table_args__ = (
        Index("work_orders_status_idx", "status"),
        Index(
            "work_orders_alert_id_key",
            "alert_id",
            unique=True,
            postgresql_where=text("alert_id is not null"),
            sqlite_where=text("alert_id is not null"),
        ),
        CheckConstraint(
            "failure_mode in ('TWF', 'HDF', 'PWF', 'OSF', 'RNF', 'OTHER')",
            name="work_orders_failure_mode_check",
        ),
    )

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
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="OPEN"
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="MEDIUM"
    )
    assigned_to: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FR7: the alert this work order was raised from (one work order per
    # alert, enforced by a partial unique index).
    alert_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    # FR9 closure record.
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # ML ground truth (ADR-0006): was this a real failure, and which mode.
    failure_confirmed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    failure_mode: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=SERVER_NOW,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=SERVER_NOW,
    )
