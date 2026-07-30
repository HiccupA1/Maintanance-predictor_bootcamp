"""Seed deterministic sample work-order data for local development.

Run this script from the backend project directory after applying migrations:

    python scripts/seed_sample_data.py

The fixed identifiers make the operation safe to run repeatedly. Existing
records are preserved, so the command will not create duplicate work orders.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

# Ensure ``app`` can be imported when this file is launched directly from any
# working directory, including Windows shells outside the backend directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.equipment import Equipment
from app.models.work_order import WorkOrder

SAMPLE_EQUIPMENT_ID = "sample-pump-001"
SAMPLE_EQUIPMENT_ROW_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SAMPLE_ALERT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
SAMPLE_WORK_ORDER_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


# PUBLIC_INTERFACE
def seed_sample_data() -> None:
    """Insert deterministic sample equipment, alert, and work-order records.

    The operation is idempotent. Existing records with the sample identifiers
    are left unchanged, allowing developers to rerun the command safely.
    """
    db = SessionLocal()
    try:
        equipment = db.get(Equipment, SAMPLE_EQUIPMENT_ROW_ID)
        if equipment is None:
            equipment = Equipment(
                id=SAMPLE_EQUIPMENT_ROW_ID,
                equipment_id=SAMPLE_EQUIPMENT_ID,
                name="Cooling Water Pump",
                location="Plant 1 / North Bay",
                type="Centrifugal pump",
                criticality=4,
            )
            db.add(equipment)
            db.flush()

        alert = db.get(Alert, SAMPLE_ALERT_ID)
        if alert is None:
            alert = Alert(
                id=SAMPLE_ALERT_ID,
                equipment_id=SAMPLE_EQUIPMENT_ROW_ID,
                status="NEW",
                priority="HIGH",
                issuer_name="Local Development",
                current_value="9.5",
                breach_timestamp=datetime.now(timezone.utc),
                suggested_action="Inspect pump bearings and vibration source.",
                why_priority="Elevated vibration may indicate bearing wear.",
                machine_details={
                    "model": "PUMP-X",
                    "asset_tag": SAMPLE_EQUIPMENT_ID,
                },
                readings_snapshot={"vibration": 9.5, "unit": "mm/s"},
            )
            db.add(alert)
            db.flush()

        work_order = db.get(WorkOrder, SAMPLE_WORK_ORDER_ID)
        if work_order is None:
            work_order = db.scalar(
                select(WorkOrder).where(WorkOrder.alert_id == SAMPLE_ALERT_ID)
            )

        if work_order is None:
            work_order = WorkOrder(
                id=SAMPLE_WORK_ORDER_ID,
                alert_id=SAMPLE_ALERT_ID,
                equipment_id=SAMPLE_EQUIPMENT_ROW_ID,
                description=(
                    "Inspect cooling water pump vibration and verify bearing "
                    "condition."
                ),
                priority="HIGH",
                status="OPEN",
                issuer_name="Local Development",
                machine_details={
                    "model": "PUMP-X",
                    "asset_tag": SAMPLE_EQUIPMENT_ID,
                },
                readings_snapshot={"vibration": 9.5, "unit": "mm/s"},
            )
            db.add(work_order)

        db.commit()
        print(
            "Sample work order is ready: "
            f"{work_order.id} ({work_order.description})"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# PUBLIC_INTERFACE
def main() -> None:
    """Run the local sample-data seed operation."""
    seed_sample_data()


if __name__ == "__main__":
    main()
