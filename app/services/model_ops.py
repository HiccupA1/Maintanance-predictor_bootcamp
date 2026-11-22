"""Model operations: shadow evaluation and drift monitoring (WP5).

Both are computed from data the system already records:

- ``risk_scores``: every score, with the exact feature vector used.
- Work orders closed with ``failure_confirmed``: the ground truth (FR9).
- Threshold alerts: the existing rule-based baseline the model must beat.

**Failure event.** A work order closed with ``failure_confirmed = true``,
timed at the work order's ``created_at`` (when the problem was raised). A
warning counts only if it came *before* the event, within ``horizon``.

**Alert episodes.** Consecutive flagged scores on one equipment form one
episode, so a model that re-flags the same machine every reading is not
credited (or penalised) once per reading. An episode is a true positive if
a failure event follows within ``horizon`` of its last flagged score.
Episodes whose horizon has not yet elapsed are *pending* and are excluded
from precision (right-censoring).
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.ml import ModelVersion, RiskScore
from app.models.work_order import WorkOrder

PSI_MODERATE = 0.1
PSI_SIGNIFICANT = 0.25
MIN_DRIFT_SAMPLES = 30


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass
class _Episode:
    equipment_id: str
    start: datetime
    end: datetime


def _episodes(points: list[tuple[str, datetime, bool]]) -> list[_Episode]:
    """Group flagged scores into runs per equipment."""
    episodes: list[_Episode] = []
    current: dict[str, _Episode | None] = {}
    for equipment_id, ts, flagged in sorted(
        points, key=lambda p: (p[0], p[1])
    ):
        open_episode = current.get(equipment_id)
        if flagged:
            if open_episode is None:
                open_episode = _Episode(equipment_id, ts, ts)
                episodes.append(open_episode)
                current[equipment_id] = open_episode
            else:
                open_episode.end = ts
        else:
            current[equipment_id] = None
    return episodes


def _confirmed_failures(
    db: Session, equipment_ids: set[str], since: datetime
) -> dict[str, list[datetime]]:
    rows = db.execute(
        select(WorkOrder.equipment_id, WorkOrder.created_at).where(
            WorkOrder.failure_confirmed.is_(True),
            WorkOrder.equipment_id.in_(equipment_ids),
        )
    ).all()
    events: dict[str, list[datetime]] = {}
    for equipment_id, created_at in rows:
        ts = _utc(created_at)
        if ts >= since:
            events.setdefault(str(equipment_id), []).append(ts)
    return events


def _score_warnings(
    warnings: list[tuple[str, datetime, datetime]],
    events: dict[str, list[datetime]],
    horizon: timedelta,
    now: datetime,
) -> dict:
    """Precision over warnings, recall and lead time over failure events.

    ``warnings`` are (equipment_id, first_warning_at, last_warning_at).
    """
    tp = fp = pending = 0
    for equipment_id, _first, last in warnings:
        hit = any(
            last < t <= last + horizon for t in events.get(equipment_id, [])
        )
        if hit:
            tp += 1
        elif last + horizon > now:
            pending += 1
        else:
            fp += 1

    total_events = sum(len(v) for v in events.values())
    detected = 0
    lead_hours: list[float] = []
    for equipment_id, times in events.items():
        for t in times:
            leads = [
                (t - first).total_seconds() / 3600
                for eq, first, last in warnings
                if eq == equipment_id and t - horizon <= last < t
            ]
            if leads:
                detected += 1
                lead_hours.append(max(leads))
    decided = tp + fp
    return {
        "warnings": len(warnings),
        "true_positive": tp,
        "false_positive": fp,
        "pending": pending,
        "precision": round(tp / decided, 4) if decided else None,
        "failures": total_events,
        "failures_detected": detected,
        "recall": round(detected / total_events, 4) if total_events else None,
        "median_lead_hours": (
            round(median(lead_hours), 1) if lead_hours else None
        ),
    }


def evaluate_version(
    db: Session,
    version: ModelVersion,
    *,
    days: int = 90,
    horizon_days: int = 7,
    now: datetime | None = None,
) -> dict:
    """Compare a version's warnings, and the threshold alerts, with
    confirmed failures over the last ``days``."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    horizon = timedelta(days=horizon_days)

    rows = db.execute(
        select(
            RiskScore.equipment_id, RiskScore.scored_at, RiskScore.flagged
        ).where(RiskScore.model_version_id == version.id)
    ).all()
    points = [
        (str(e), _utc(ts), bool(f)) for e, ts, f in rows if _utc(ts) >= since
    ]
    equipment_ids = {p[0] for p in points}
    events = _confirmed_failures(db, equipment_ids, since) if points else {}

    model = _score_warnings(
        [(e.equipment_id, e.start, e.end) for e in _episodes(points)],
        events,
        horizon,
        now,
    )

    alerts = db.execute(
        select(Alert.equipment_id, Alert.created_at).where(
            Alert.source == "THRESHOLD",
            Alert.equipment_id.in_(equipment_ids),
        )
    ).all()
    baseline = _score_warnings(
        [
            (str(e), _utc(ts), _utc(ts))
            for e, ts in alerts
            if e is not None and _utc(ts) >= since
        ],
        events,
        horizon,
        now,
    )

    return {
        "model_version": version.version,
        "stage": version.stage,
        "window_days": days,
        "horizon_days": horizon_days,
        "scores": len(points),
        "equipment": len(equipment_ids),
        "model": model,
        "threshold_alerts": baseline,
        "notes": [
            "Failures are work orders closed with failure_confirmed; "
            "unlabelled closures are not counted as failures.",
            "Pending warnings are excluded from precision until their "
            "horizon has elapsed.",
        ],
    }


# Drift -------------------------------------------------------------------


def psi(reference: dict, values: list[float]) -> float:
    """Population Stability Index of ``values`` against a reference
    histogram ``{"edges": [...], "proportions": [...]}``."""
    edges = reference["edges"]
    counts = [0] * (len(edges) + 1)
    for value in values:
        counts[bisect_left(edges, value)] += 1
    eps = 1e-4
    total = 0.0
    for ref, count in zip(reference["proportions"], counts, strict=True):
        cur = max(count / len(values), eps)
        ref = max(ref, eps)
        total += (cur - ref) * math.log(cur / ref)
    return round(total, 4)


def _level(value: float) -> str:
    if value >= PSI_SIGNIFICANT:
        return "significant"
    if value >= PSI_MODERATE:
        return "moderate"
    return "stable"


def drift_version(
    db: Session,
    version: ModelVersion,
    *,
    days: int = 7,
    now: datetime | None = None,
) -> dict:
    """PSI of recent inputs and scores against the training reference."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    reference = (version.metrics or {}).get("reference")
    base = {"model_version": version.version, "window_days": days}
    if not reference:
        return {**base, "status": "no_reference", "features": {}}

    rows = db.execute(
        select(RiskScore.features, RiskScore.score, RiskScore.scored_at).where(
            RiskScore.model_version_id == version.id
        )
    ).all()
    recent = [(f, s) for f, s, ts in rows if _utc(ts) >= since]
    if len(recent) < MIN_DRIFT_SAMPLES:
        return {
            **base,
            "status": "insufficient_data",
            "samples": len(recent),
            "min_samples": MIN_DRIFT_SAMPLES,
            "features": {},
        }

    features = {}
    for name, ref in reference["features"].items():
        values = [float(f[name]) for f, _ in recent if name in f]
        if values:
            value = psi(ref, values)
            features[name] = {"psi": value, "level": _level(value)}
    score_psi = psi(reference["score"], [float(s) for _, s in recent])
    levels = [v["level"] for v in features.values()] + [_level(score_psi)]
    status = (
        "significant"
        if "significant" in levels
        else "moderate" if "moderate" in levels else "stable"
    )
    return {
        **base,
        "status": status,
        "samples": len(recent),
        "score": {"psi": score_psi, "level": _level(score_psi)},
        "features": features,
        "thresholds": {
            "moderate": PSI_MODERATE,
            "significant": PSI_SIGNIFICANT,
        },
    }
