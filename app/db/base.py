"""SQLAlchemy declarative base and shared column types.

Defines the declarative ``Base`` used by all ORM models and a JSON column type
that maps to native ``JSONB`` on PostgreSQL while degrading to generic ``JSON``
on other backends (e.g., SQLite used in tests).
"""

import uuid

from sqlalchemy import JSON, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


# PUBLIC_INTERFACE
class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


# JSON type: JSONB on PostgreSQL, generic JSON everywhere else.
JSONType = JSON().with_variant(JSONB, "postgresql")

# Server-side defaults expressed as SQL *expressions*, not string literals.
# A plain string passed to ``server_default`` is rendered as a quoted literal
# (e.g. ``DEFAULT 'now()'``), which is wrong on every backend.
# ``func.now()`` renders as ``now()`` on PostgreSQL and ``CURRENT_TIMESTAMP``
# on SQLite; the parenthesised UUID expression is valid DDL on both.
SERVER_NOW = func.now()
SERVER_UUID = text("(gen_random_uuid())")


# PUBLIC_INTERFACE
def new_uuid() -> str:
    """Return a new random UUID string for client-side primary keys."""
    return str(uuid.uuid4())
