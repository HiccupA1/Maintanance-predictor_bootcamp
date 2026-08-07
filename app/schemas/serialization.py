"""Shared schema-level serialization/validation helpers.

This module centralizes the response-model coercion pattern used across the API:
- UUID-like identifiers are coerced to strings (API contract exposes ids as str)
- timezone-naive datetimes are normalized to UTC-aware values

Centralizing this logic prevents each schema from re-implementing identical
validators and keeps the "response validation must not 500" guarantee consistent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID


# PUBLIC_INTERFACE
def coerce_uuid_to_str(value: object) -> str:
    """Coerce UUID-like identifiers into string form.

    Args:
        value: Any value, possibly a uuid.UUID instance.

    Returns:
        str: The UUID string if `value` is a UUID, otherwise the original value
        (assumed str-like) cast to str by Pydantic as needed.
    """
    if isinstance(value, UUID):
        return str(value)
    return value  # type: ignore[return-value]


# PUBLIC_INTERFACE
def coerce_optional_uuid_to_str(value: object) -> str | None:
    """Coerce optional UUID-like identifiers into string form.

    Args:
        value: Any value, possibly None or a uuid.UUID instance.

    Returns:
        str | None: None if value is None; otherwise UUID string if UUID; else
        the original value (assumed str-like) for Pydantic to handle.
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    return value  # type: ignore[return-value]


# PUBLIC_INTERFACE
def normalize_datetime_to_utc(value: object) -> datetime:
    """Normalize a datetime to be timezone-aware (UTC) when tzinfo is missing.

    Args:
        value: Any value, expected to be a datetime in practice.

    Returns:
        datetime: If tz-naive, returns the same datetime with tzinfo=UTC.
        Otherwise returns the original value.
    """
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value  # type: ignore[return-value]


# PUBLIC_INTERFACE
def normalize_optional_datetime_to_utc(value: object) -> datetime | None:
    """Normalize an optional datetime to be timezone-aware (UTC) when tzinfo is missing.

    Args:
        value: Any value, possibly None or a datetime.

    Returns:
        datetime | None: None if value is None; otherwise normalized datetime.
    """
    if value is None:
        return None
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value  # type: ignore[return-value]
