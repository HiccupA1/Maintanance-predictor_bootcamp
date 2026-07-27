"""WorkOrderPartLine ORM model.

Represents a spare-part line attached to a work order. Per MVP scope there is no
quantity field; a ``used`` flag and free-text ``notes`` capture whether a part
was used and any additional context.
"""

from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    """Return a new UUID4 as a string."""
    return str(uuid4())


class WorkOrderPartLine(Base):
    """A single spare-part line item on a work order."""

    __tablename__ = "work_order_part_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    work_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_orders.id"), nullable=False
    )
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_order = relationship("WorkOrder", back_populates="parts")
