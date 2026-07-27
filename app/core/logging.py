"""Logging configuration with correlation-id support.

Provides a minimal structured logging setup. A per-request correlation id is
stored in a context variable so log lines and error responses can be tied to a
single request without threading the id through every function signature.
"""

import logging
import sys
from contextvars import ContextVar
from uuid import uuid4

# Context variable holding the current request correlation id.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


# PUBLIC_INTERFACE
def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the application.

    Args:
        level: The logging level to apply to the root logger.
    """
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g., under pytest/uvicorn reload); do nothing.
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] "
        "[cid=%(correlation_id)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(_CorrelationIdFilter())
    root.addHandler(handler)
    root.setLevel(level)


class _CorrelationIdFilter(logging.Filter):
    """Inject the current correlation id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.correlation_id = get_correlation_id() or "-"
        return True


# PUBLIC_INTERFACE
def set_correlation_id(value: str | None = None) -> str:
    """Set the correlation id for the current context.

    Args:
        value: An explicit correlation id. When omitted, a new UUID4 is used.

    Returns:
        str: The correlation id that was set.
    """
    cid = value or str(uuid4())
    _correlation_id.set(cid)
    return cid


# PUBLIC_INTERFACE
def get_correlation_id() -> str:
    """Return the correlation id bound to the current context.

    Returns:
        str: The current correlation id, or an empty string if unset.
    """
    return _correlation_id.get()
