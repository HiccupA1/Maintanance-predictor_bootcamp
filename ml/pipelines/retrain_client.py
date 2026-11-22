"""Retrain on the client's own confirmed failures (WP5, ADR-0006).

    python -m ml.pipelines.retrain_client --asset-class ai4i_milling \
        --version client-v1 [--horizon-days 7] [--min-failures 30]

**Dataset.** Every stored risk score already carries the exact feature
vector used at scoring time. A row is labelled 1 if a confirmed failure (a
work order closed with ``failure_confirmed``, timed at its ``created_at``)
followed on the same equipment within ``horizon``. Rows whose horizon has
not yet elapsed are dropped, because their label is not known yet.

**Gate.** Training only proceeds once at least ``--min-failures`` distinct
confirmed failures exist (the ADR-0006 retraining trigger).

**Protocol.** The split is by time, never random, since the model will be
used on the future:
- train: oldest 60%;
- validation: next 15%, used to choose the threshold;
- holdout: newest 25%, used once to compare challenger and champion.

The challenger is written out **only if it beats the champion** (the active
version, or else the newest shadow) on holdout PR-AUC by ``--margin``. It is
then registered in shadow like any other model (``ml.scripts.register_model``).

Exit codes: 0 challenger written, 3 not enough labels, 4 champion kept.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml import ModelVersion, RiskScore
from app.models.work_order import WorkOrder
from app.services import model_registry
from ml.config import ARTIFACTS_DIR, RECALL_FLOOR, SEED
from ml.evaluation import choose_threshold, evaluate, tradeoff
from ml.features.ai4i import FEATURES
from ml.reference import build_reference

INSUFFICIENT_LABELS = 3
CHAMPION_KEPT = 4


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def build_dataset(
    db: Session, asset_class: str, horizon_days: int, now: datetime
) -> tuple[pd.DataFrame, int]:
    """Labelled rows from stored scores, and the confirmed-failure count."""
    horizon = timedelta(days=horizon_days)
    rows = db.execute(
        select(RiskScore.equipment_id, RiskScore.scored_at, RiskScore.features)
        .join(ModelVersion, ModelVersion.id == RiskScore.model_version_id)
        .where(ModelVersion.asset_class == asset_class)
    ).all()
    # Several versions can score the same reading: keep one row per event.
    seen: dict[tuple[str, datetime], dict] = {}
    for equipment_id, scored_at, features in rows:
        seen.setdefault((str(equipment_id), _utc(scored_at)), features)

    equipment_ids = {k[0] for k in seen}
    events: dict[str, list[datetime]] = {}
    for equipment_id, created_at in db.execute(
        select(WorkOrder.equipment_id, WorkOrder.created_at).where(
            WorkOrder.failure_confirmed.is_(True),
            WorkOrder.equipment_id.in_(equipment_ids),
        )
    ).all():
        events.setdefault(str(equipment_id), []).append(_utc(created_at))

    records = []
    for (equipment_id, ts), features in seen.items():
        if ts + horizon > now:
            continue  # outcome not yet observable
        label = any(
            ts < t <= ts + horizon for t in events.get(equipment_id, [])
        )
        records.append(
            {
                "equipment_id": equipment_id,
                "scored_at": ts,
                "label": int(label),
                **{f: float(features[f]) for f in FEATURES},
            }
        )
    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df = df.sort_values("scored_at").reset_index(drop=True)
    return df, sum(len(v) for v in events.values())


def _champion(db: Session, asset_class: str) -> ModelVersion | None:
    for stage in ("active", "shadow"):
        version = (
            db.execute(
                select(ModelVersion)
                .where(
                    ModelVersion.asset_class == asset_class,
                    ModelVersion.kind == "failure_risk",
                    ModelVersion.stage == stage,
                )
                .order_by(ModelVersion.created_at.desc())
            )
            .scalars()
            .first()
        )
        if version is not None:
            return version
    return None


def retrain(
    db: Session,
    *,
    asset_class: str,
    version: str,
    horizon_days: int = 7,
    min_failures: int = 30,
    margin: float = 0.01,
    out_dir: Path = ARTIFACTS_DIR,
    now: datetime | None = None,
) -> tuple[int, dict]:
    now = now or datetime.now(timezone.utc)
    df, failures = build_dataset(db, asset_class, horizon_days, now)
    report: dict = {
        "version": version,
        "asset_class": asset_class,
        "horizon_days": horizon_days,
        "rows": int(len(df)),
        "confirmed_failures": failures,
        "min_failures": min_failures,
    }
    if failures < min_failures or df.empty:
        report["decision"] = "insufficient_labels"
        return INSUFFICIENT_LABELS, report

    n = len(df)
    train = df.iloc[: int(n * 0.60)]
    val = df.iloc[int(n * 0.60) : int(n * 0.75)]
    holdout = df.iloc[int(n * 0.75) :]
    for name, part in (
        ("train", train),
        ("validation", val),
        ("holdout", holdout),
    ):
        if part["label"].nunique() < 2:
            report["decision"] = "insufficient_labels"
            report["detail"] = f"{name} period has only one class"
            return INSUFFICIENT_LABELS, report

    challenger = CalibratedClassifierCV(
        HistGradientBoostingClassifier(
            class_weight="balanced",
            learning_rate=0.05,
            max_iter=300,
            random_state=SEED,
        ),
        method="isotonic",
        cv=3,
    ).fit(train[FEATURES], train["label"])
    val_scores = challenger.predict_proba(val[FEATURES])[:, 1]
    threshold, rule = choose_threshold(
        val["label"].to_numpy(), val_scores, RECALL_FLOOR
    )

    y_hold = holdout["label"].to_numpy()
    chall_scores = challenger.predict_proba(holdout[FEATURES])[:, 1]
    comparison = {
        "holdout_rows": int(len(holdout)),
        "holdout_positives": int(y_hold.sum()),
        "holdout_period": [
            holdout["scored_at"].iloc[0].isoformat(),
            holdout["scored_at"].iloc[-1].isoformat(),
        ],
        "challenger": evaluate(y_hold, chall_scores, threshold),
    }
    champion = _champion(db, asset_class)
    champion_pr_auc = 0.0
    if champion is not None:
        bundle = model_registry.load(champion)
        champ_scores = bundle["model"].predict_proba(
            holdout[list(champion.features)]
        )[:, 1]
        comparison["champion"] = {
            "version": champion.version,
            "stage": champion.stage,
            **evaluate(y_hold, champ_scores, champion.threshold),
        }
        champion_pr_auc = float(average_precision_score(y_hold, champ_scores))
    challenger_pr_auc = float(average_precision_score(y_hold, chall_scores))
    better = challenger_pr_auc >= champion_pr_auc + margin
    comparison["margin"] = margin
    report["comparison"] = comparison
    report["threshold_rule"] = rule
    report["decision"] = "challenger_better" if better else "keep_champion"
    if not better:
        return CHAMPION_KEPT, report

    report["operating_points"] = tradeoff(val["label"].to_numpy(), val_scores)
    report["reference"] = build_reference(
        train[FEATURES], challenger.predict_proba(train[FEATURES])[:, 1]
    )
    report["trained_at"] = now.isoformat(timespec="seconds")
    target = out_dir / version
    target.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": challenger,
            "features": FEATURES,
            "threshold": threshold,
            "version": version,
            "kind": "failure_risk",
            "asset_class": asset_class,
        },
        target / "model.joblib",
    )
    (target / "metrics.json").write_text(
        json.dumps(report, indent=2, default=str)
    )
    return 0, report


def main() -> int:
    from app.db.session import SessionLocal

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--asset-class", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--min-failures", type=int, default=30)
    parser.add_argument("--margin", type=float, default=0.01)
    args = parser.parse_args()
    db = SessionLocal()
    try:
        code, report = retrain(
            db,
            asset_class=args.asset_class,
            version=args.version,
            horizon_days=args.horizon_days,
            min_failures=args.min_failures,
            margin=args.margin,
        )
    finally:
        db.close()
    print(
        json.dumps(
            {k: v for k, v in report.items() if k != "reference"},
            indent=2,
            default=str,
        )
    )
    if code == 0:
        print(
            f"\nNext: python -m ml.scripts.register_model "
            f"{ARTIFACTS_DIR / args.version}  (registers in shadow)"
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
