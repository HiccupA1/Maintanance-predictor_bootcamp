"""Failure-risk scoring for equipment (WP4, ADR-0006).

Flow, per equipment with an ``asset_class``:

1. Collect the latest reading of each parameter that has a ``feature_key``.
2. If any required input is missing or non-numeric, the equipment is
   **not scorable**: nothing is imputed and nothing is written.
3. Build features with the same code used in training
   (``ml.features.ai4i``), then score with every shadow or active model
   registered for that asset class.
4. Store every score in ``risk_scores``. Only **active** models raise or
   resolve ``MODEL`` alerts; shadow scores are never shown to non-admins.

Scoring currently runs in the request that records a reading. That is
acceptable at manual-entry volumes; the telemetry worker (WP2, ADR-0004)
calls the same ``score_equipment``. Failures are logged and never fail the
reading itself.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.model_inputs import CATEGORICAL_KEYS, FEATURE_KEYS
from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter, Reading
from app.models.ml import ModelVersion, RiskScore
from app.services import model_registry

logger = logging.getLogger(__name__)

ACTIVE_ALERT_STATUSES = ("NEW", "IN_PROGRESS")


@dataclass(frozen=True)
class ScoreOutcome:
    """What happened when scoring was attempted."""

    status: str  # scored | not_configured | not_scorable | disabled | error
    detail: str = ""
    scores: tuple[RiskScore, ...] = ()


def latest_inputs(db: Session, equipment: Equipment) -> dict[str, object]:
    """Latest reading value for each mapped parameter, keyed by feature."""
    latest = (
        select(
            Reading.parameter_id,
            func.max(Reading.timestamp).label("ts"),
        )
        .where(Reading.equipment_id == equipment.id)
        .group_by(Reading.parameter_id)
        .subquery()
    )
    rows = db.execute(
        select(Parameter.feature_key, Reading.value)
        .join(Reading, Reading.parameter_id == Parameter.id)
        .join(
            latest,
            (latest.c.parameter_id == Reading.parameter_id)
            & (latest.c.ts == Reading.timestamp),
        )
        .where(
            Parameter.equipment_id == equipment.id,
            Parameter.feature_key.is_not(None),
        )
    ).all()
    values: dict[str, object] = {}
    for key, raw in rows:
        if key in CATEGORICAL_KEYS:
            values[key] = str(raw).strip().upper()
        else:
            try:
                values[key] = float(raw)
            except (TypeError, ValueError):
                continue  # non-numeric reading: treated as missing
    return values


def _sync_model_alert(
    db: Session,
    equipment: Equipment,
    version: ModelVersion,
    score: float,
    flagged: bool,
) -> None:
    alert = db.execute(
        select(Alert).where(
            Alert.equipment_id == equipment.id,
            Alert.source == "MODEL",
            Alert.status.in_(ACTIVE_ALERT_STATUSES),
        )
    ).scalar_one_or_none()
    if flagged:
        why = (
            f"Failure risk {score:.0%} from model {version.version} "
            f"(alert threshold {version.threshold:.0%})."
        )
        if alert is None:
            db.add(
                Alert(
                    equipment_id=equipment.id,
                    source="MODEL",
                    status="NEW",
                    priority="CRITICAL" if score >= 0.8 else "HIGH",
                    current_value=f"{score:.3f}",
                    why_priority=why,
                    suggested_action=(
                        "Inspect before the next run; confirm or reject the "
                        "failure when closing the work order."
                    ),
                )
            )
        else:
            alert.current_value = f"{score:.3f}"
            alert.why_priority = why
    elif alert is not None:
        alert.status = "RESOLVED"


def score_equipment(db: Session, equipment: Equipment) -> ScoreOutcome:
    """Score one equipment with all shadow/active models for its class."""
    if not get_settings().scoring_enabled:
        return ScoreOutcome("disabled")
    if not equipment.asset_class:
        return ScoreOutcome("not_configured", "equipment has no asset_class")

    versions = (
        db.execute(
            select(ModelVersion).where(
                ModelVersion.asset_class == equipment.asset_class,
                ModelVersion.kind == "failure_risk",
                ModelVersion.stage.in_(("shadow", "active")),
            )
        )
        .scalars()
        .all()
    )
    if not versions:
        return ScoreOutcome("not_configured", "no model for asset_class")

    inputs = latest_inputs(db, equipment)
    missing = [k for k in FEATURE_KEYS if k not in inputs]
    if missing:
        return ScoreOutcome("not_scorable", f"missing inputs: {missing}")

    try:
        import pandas as pd

        from ml.features.ai4i import build_features
    except ImportError:  # API deployed without the ml extra
        logger.warning("scoring skipped: ml extra not installed")
        return ScoreOutcome("disabled", "ml extra not installed")

    try:
        features = build_features(pd.DataFrame([inputs]))
    except ValueError as exc:
        return ScoreOutcome("not_scorable", str(exc))

    scored_at = datetime.now(timezone.utc)
    scores = []
    for version in versions:
        bundle = model_registry.load(version)
        row = features[list(version.features)]
        score = float(bundle["model"].predict_proba(row)[0, 1])
        flagged = score >= version.threshold
        record = RiskScore(
            equipment_id=equipment.id,
            model_version_id=version.id,
            score=score,
            flagged=flagged,
            stage=version.stage,
            features={k: float(v) for k, v in row.iloc[0].items()},
            scored_at=scored_at,
        )
        db.add(record)
        scores.append(record)
        if version.stage == "active":
            _sync_model_alert(db, equipment, version, score, flagged)
    db.commit()
    return ScoreOutcome("scored", scores=tuple(scores))


def score_after_reading(db: Session, equipment_id: str) -> ScoreOutcome:
    """Best-effort hook used by reading writes. Never raises."""
    try:
        equipment = db.get(Equipment, equipment_id)
        if equipment is None:
            return ScoreOutcome("not_configured", "equipment missing")
        return score_equipment(db, equipment)
    except Exception:  # noqa: BLE001 - scoring must not fail the reading
        db.rollback()
        logger.exception("risk scoring failed for equipment %s", equipment_id)
        return ScoreOutcome("error")
