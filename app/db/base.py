"""SQLAlchemy declarative base and shared column types.

Defines the declarative ``Base`` used by all ORM models and a JSON column type
that maps to native ``JSONB`` on PostgreSQL while degrading to generic ``JSON``
on other backends (e.g., SQLite used in tests).
"""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


# PUBLIC_INTERFACE
class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


# JSON type: JSONB on PostgreSQL, generic JSON everywhere else.
JSONType = JSON().with_variant(JSONB, "postgresql")
