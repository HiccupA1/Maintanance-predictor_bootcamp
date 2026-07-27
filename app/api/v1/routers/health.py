"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.db.session import get_db

router = APIRouter(tags=["health"])


# PUBLIC_INTERFACE
@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return a simple liveness payload.

    Returns:
        dict: ``{"status": "ok"}`` when the service is running.
    """
    return {"status": "ok"}


# PUBLIC_INTERFACE
@router.get("/health/db", summary="Database readiness probe")
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Check database connectivity with a trivial ``SELECT 1``.

    Args:
        db: Injected database session.

    Returns:
        dict: ``{"status": "ok", "database": "ok"}`` when reachable.

    Raises:
        ProblemException: ``dependency_unavailable`` (503) if the DB is down.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - surface as dependency problem
        raise ProblemException(
            status=503,
            code=ErrorCode.DEPENDENCY_UNAVAILABLE,
            detail="Database is not reachable.",
        ) from exc
    return {"status": "ok", "database": "ok"}
