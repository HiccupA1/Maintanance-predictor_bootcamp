"""Pytest fixtures for the Work Order Management backend.

Configures an in-memory SQLite database (via ``DATABASE_URL``) before importing
the application, creates the schema from the ORM metadata, seeds a known alert,
and exposes a FastAPI ``TestClient``.
"""

import os

# Configure the DB URL BEFORE importing app modules so the engine binds to
# an in-memory SQLite database shared across connections.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.alert import Alert  # noqa: E402

SEEDED_ALERT_ID = "11111111-1111-1111-1111-111111111111"
SECOND_ALERT_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(autouse=True)
def _reset_database():
    """Recreate a clean schema and seed alerts before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(
            Alert(
                id=SEEDED_ALERT_ID,
                equipment_id="eq-1111",
                status="NEW",
                issuer_name="Alice Operator",
                machine_details={"model": "PUMP-X"},
                readings_snapshot={"vibration": 9.5},
            )
        )
        db.add(
            Alert(
                id=SECOND_ALERT_ID,
                equipment_id="eq-2222",
                status="NEW",
                issuer_name="Bob Operator",
            )
        )
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client bound to the app."""
    return TestClient(app)
