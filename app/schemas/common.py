"""Shared schema primitives.

Defines the constrained, uppercase enumerations required by the contract:

* priority: ``CRITICAL``, ``HIGH``, ``MEDIUM``
* status: ``OPEN``, ``CLOSED``
"""

from enum import Enum


# PUBLIC_INTERFACE
class Priority(str, Enum):
    """Work order priority (uppercase, constrained)."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


# PUBLIC_INTERFACE
class WorkOrderStatus(str, Enum):
    """Work order lifecycle status (uppercase, constrained)."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
