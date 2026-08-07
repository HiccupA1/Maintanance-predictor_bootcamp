"""WorkOrder ORM model.

Reconciled to the live Supabase PostgreSQL schema (public.work_orders):
- No alert_id column exists in live DB (alerts and work_orders are not FK-linked).
- work_orders has title (required), description (nullable), assigned_to, closed_by.
- equipment_id is nullable UUID with ON DELETE SET NULL.
- status/priority are TEXT defaults 'OPEN'/'MEDIUM'.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkOrder(Base):
    """A work order representing a maintenance task."""

    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    equipment_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("equipment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="'OPEN'::text", index=True
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="'MEDIUM'::text", index=True
    )
    assigned_to: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    equipment = relationship("Equipment", viewonly=True)

    @property
    def equipment_name(self) -> str | None:
        """Return the linked equipment's human-readable name when available."""
        return self.equipment.name if self.equipment is not None else None
