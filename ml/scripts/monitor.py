"""Scheduled model check: drift and shadow evaluation for live versions.

    python -m ml.scripts.monitor [--days 7] [--horizon-days 7]

Prints a JSON report for every shadow and active version. Exits 2 if any
version shows significant drift, so a scheduler (cron, GitHub Actions
schedule, or the WP2 worker) can alert operations on a non-zero exit.
"""

from __future__ import annotations

import argparse
import json
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ml import ModelVersion
from app.services import model_ops


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--eval-days", type=int, default=90)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        versions = db.execute(
            select(ModelVersion).where(
                ModelVersion.stage.in_(("shadow", "active"))
            )
        ).scalars()
        report = [
            {
                "drift": model_ops.drift_version(db, v, days=args.days),
                "evaluation": model_ops.evaluate_version(
                    db, v, days=args.eval_days, horizon_days=args.horizon_days
                ),
            }
            for v in versions
        ]
    finally:
        db.close()
    print(json.dumps(report, indent=2, default=str))
    return (
        2 if any(r["drift"]["status"] == "significant" for r in report) else 0
    )


if __name__ == "__main__":
    sys.exit(main())
