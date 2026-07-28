"""Alert repository (data access for the Alert MVP stub)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert


# PUBLIC_INTERFACE
def get_alert(db: Session, alert_id: str) -> Alert | None:
    """Fetch an alert by id.

    Args:
        db: Active database session.
        alert_id: UUID string of the alert.

    Returns:
        Alert | None: The alert if found, otherwise ``None``.
    """
    return db.execute(
        select(Alert).where(Alert.id == alert_id)
    ).scalar_one_or_none()
