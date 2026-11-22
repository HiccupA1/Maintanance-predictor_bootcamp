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


# PUBLIC_INTERFACE
class FailureMode(str, Enum):
    """Failure mode recorded at work-order closure (ML label, ADR-0006).

    Mirrors the AI4I 2020 modes so labels map onto the bootstrap model:
    tool wear (TWF), heat dissipation (HDF), power (PWF), overstrain (OSF),
    random (RNF), plus OTHER for anything outside that taxonomy.
    """

    TWF = "TWF"
    HDF = "HDF"
    PWF = "PWF"
    OSF = "OSF"
    RNF = "RNF"
    OTHER = "OTHER"
