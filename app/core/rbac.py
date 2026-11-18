"""Server-side authorization policy.

This module is the single source of truth for which application role may
perform which action. Routes declare a *permission*, never a role list, so the
policy can be reviewed (and changed) in one place. The same table is documented
in ``Docs/security/authorization-matrix.md`` and exercised route by route in
``tests/test_authorization.py``.

The frontend hides controls by role (``frontend/src/utils/rbac.ts``), but that
is a usability measure only; these checks are the enforcement point.
"""

from __future__ import annotations

from enum import Enum

from fastapi import Depends

from app.core.auth import require_roles


class Role(str, Enum):
    """Application roles persisted in ``user_profiles.role``."""

    ADMIN = "Admin"
    PLANT_MANAGER = "PlantManager"
    OPERATOR = "Operator"
    MAINTENANCE_ENGINEER = "MaintenanceEngineer"


ALL_ROLES = frozenset(Role)
# Roles that work the alert and work-order queues (frontend `operationalRoles`).
OPERATIONAL_ROLES = frozenset(
    {Role.ADMIN, Role.PLANT_MANAGER, Role.MAINTENANCE_ENGINEER}
)


class Permission(str, Enum):
    """Actions that routes are guarded by."""

    EQUIPMENT_READ = "equipment:read"
    EQUIPMENT_WRITE = "equipment:write"
    EQUIPMENT_DELETE = "equipment:delete"
    PARAMETER_READ = "parameter:read"
    PARAMETER_WRITE = "parameter:write"
    READING_READ = "reading:read"
    READING_WRITE = "reading:write"
    ALERT_READ = "alert:read"
    ALERT_DELETE = "alert:delete"
    WORK_ORDER_READ = "work_order:read"
    WORK_ORDER_CREATE = "work_order:create"
    WORK_ORDER_UPDATE = "work_order:update"
    WORK_ORDER_DELETE = "work_order:delete"
    USER_ADMIN = "user:admin"


# PRD references are to Docs/stage-1/PRD-expanded.md functional requirements.
POLICY: dict[Permission, frozenset[Role]] = {
    # Every role needs equipment/parameter context (Operators pick them when
    # recording readings).
    Permission.EQUIPMENT_READ: ALL_ROLES,
    Permission.EQUIPMENT_WRITE: frozenset({Role.ADMIN}),  # FR1
    Permission.EQUIPMENT_DELETE: frozenset({Role.ADMIN}),
    Permission.PARAMETER_READ: ALL_ROLES,
    Permission.PARAMETER_WRITE: frozenset({Role.PLANT_MANAGER}),  # FR2
    Permission.READING_READ: ALL_ROLES,
    Permission.READING_WRITE: frozenset({Role.OPERATOR}),  # FR3
    Permission.ALERT_READ: OPERATIONAL_ROLES,
    Permission.ALERT_DELETE: frozenset({Role.PLANT_MANAGER}),
    Permission.WORK_ORDER_READ: OPERATIONAL_ROLES,
    Permission.WORK_ORDER_CREATE: frozenset({Role.PLANT_MANAGER}),  # FR7
    # Plant Managers edit open work orders (FR8); Maintenance Engineers close
    # them (FR9).
    Permission.WORK_ORDER_UPDATE: frozenset(
        {Role.PLANT_MANAGER, Role.MAINTENANCE_ENGINEER}
    ),
    Permission.WORK_ORDER_DELETE: frozenset(
        {Role.PLANT_MANAGER, Role.MAINTENANCE_ENGINEER}
    ),
    Permission.USER_ADMIN: frozenset({Role.ADMIN}),
}

_GUARDS = {
    permission: require_roles(role.value for role in roles)
    for permission, roles in POLICY.items()
}


# PUBLIC_INTERFACE
def require_permission(permission: Permission):
    """Return the FastAPI dependency that enforces ``permission``.

    Use it as ``dependencies=[Depends(require_permission(...))]``, or as a
    parameter default when the handler needs the authenticated profile.
    Missing or invalid credentials give 401; a valid user without one of the
    permitted roles gives 403.
    """
    return _GUARDS[permission]


# PUBLIC_INTERFACE
def guard(permission: Permission):
    """Shorthand for ``Depends(require_permission(permission))``."""
    return Depends(require_permission(permission))
