"""Database engine and session management.

Creates the SQLAlchemy engine from configuration and exposes a ``get_db``
dependency yielding a scoped session. SQLite URLs (used by the test suite) get
the connection arguments and pooling needed for an in-memory database shared
across threads.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def _build_engine():
    """Create the SQLAlchemy engine based on the configured database URL."""
    url = get_settings().database_url
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # Keep a single in-memory database alive across connections/threads.
        if ":memory:" in url or url in ("sqlite://",):
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
                future=True,
            )
        return create_engine(url, connect_args=connect_args, future=True)
    settings = get_settings()
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        # Fail fast under overload rather than queueing requests for 30 s.
        pool_timeout=settings.db_pool_timeout_s,
        future=True,
    )


engine = _build_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


# PUBLIC_INTERFACE
def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session.

    Yields:
        Session: A SQLAlchemy session that is closed when the request ends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
