"""ORM models package.

Importing this package registers all models on the shared declarative
``Base.metadata`` so migrations and table creation see the full schema.
"""

from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter, Reading
from app.models.user_profile import UserProfile
from app.models.work_order import WorkOrder
from app.models.work_order_part_line import WorkOrderPartLine

__all__ = [
    "Alert",
    "Equipment",
    "Parameter",
    "Reading",
    "UserProfile",
    "WorkOrder",
    "WorkOrderPartLine",
]
