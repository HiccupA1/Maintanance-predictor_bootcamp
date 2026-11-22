"""WP5: shadow evaluation, drift monitoring and client-label retraining."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sklearn")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.alert import Alert  # noqa: E402
from app.models.equipment import Equipment  # noqa: E402
from app.models.ml import ModelVersion, RiskScore  # noqa: E402
from app.models.work_order import WorkOrder  # noqa: E402
from app.services import model_ops, model_registry  # noqa: E402
from ml.features.ai4i import FEATURES  # noqa: E402
from ml.models import RuleBaseline  # noqa: E402
from ml.pipelines import retrain_client  # noqa: E402
from ml.reference import build_reference  # noqa: E402

NOW = datetime.now(timezone.utc).replace(microsecond=0)
EQ_A = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"
EQ_B = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2"


def _days(n: float) -> datetime:
    return NOW + timedelta(days=n)


def _features(rng: np.random.Generator, n: int, air_shift: float = 0.0):
    return pd.DataFrame(
        {
            "air_temp_k": rng.normal(300 + air_shift, 2, n),
            "process_temp_k": rng.normal(310, 1.5, n),
            "rotational_speed_rpm": rng.normal(1540, 180, n),
            "torque_nm": rng.normal(40, 10, n),
            "tool_wear_min": rng.uniform(0, 240, n),
            "temp_diff_k": rng.normal(10, 1, n),
            "power_w": rng.normal(6400, 1500, n),
            "strain_nm_min": rng.uniform(0, 12000, n),
            "type_L": rng.integers(0, 2, n).astype(float),
            "type_M": 0.0,
            "type_H": 0.0,
        }
    )[FEATURES]


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(
        model_registry,
        "get_settings",
        lambda: Settings(model_store_dir=str(tmp_path)),
    )
    model_registry.clear_cache()
    yield tmp_path
    model_registry.clear_cache()


def _version(store, *, reference: dict | None = None, stage="shadow") -> str:
    path = store / "rules.joblib"
    joblib.dump(
        {
            "model": RuleBaseline().fit(None),
            "features": FEATURES,
            "threshold": 0.25,
            "version": "rules-v1",
            "kind": "failure_risk",
            "asset_class": "ai4i_milling",
        },
        path,
    )
    db = SessionLocal()
    row = ModelVersion(
        version="rules-v1",
        asset_class="ai4i_milling",
        stage=stage,
        threshold=0.25,
        features=FEATURES,
        metrics={"reference": reference} if reference else None,
        artifact_uri=path.name,
        artifact_sha256=model_registry.sha256_file(path),
    )
    db.add(row)
    db.commit()
    version_id = row.id
    db.close()
    return version_id


def _score(
    db, version_id, equipment_id, at, flagged, features=None, score=None
):
    db.add(
        RiskScore(
            equipment_id=equipment_id,
            model_version_id=version_id,
            score=score if score is not None else (0.9 if flagged else 0.1),
            flagged=flagged,
            stage="shadow",
            features=features or {f: 0.0 for f in FEATURES},
            scored_at=at,
        )
    )


def _failure(db, equipment_id, at, confirmed=True):
    db.add(
        WorkOrder(
            title="wo",
            priority="HIGH",
            status="CLOSED",
            equipment_id=equipment_id,
            failure_confirmed=confirmed,
            failure_mode="TWF" if confirmed else None,
            created_at=at,
            closed_at=at + timedelta(hours=4),
        )
    )


# Shadow evaluation -------------------------------------------------------


def test_evaluation_counts_episodes_recall_and_lead_time(store) -> None:
    vid = _version(store)
    db = SessionLocal()
    # Equipment A: episode 1 (-30, -29) precedes a failure at -27.
    _score(db, vid, EQ_A, _days(-30), True)
    _score(db, vid, EQ_A, _days(-29), True)
    _score(db, vid, EQ_A, _days(-28), False)
    _score(db, vid, EQ_A, _days(-10), True)  # episode 2: false alarm
    _score(db, vid, EQ_B, _days(-20), True)  # episode 3: false alarm
    _score(db, vid, EQ_B, _days(-15), False)  # ends episode 3
    _score(db, vid, EQ_B, _days(-2), True)  # episode 4: horizon not elapsed
    _failure(db, EQ_A, _days(-27))
    _failure(db, EQ_B, _days(-50))  # missed by the model
    _failure(db, EQ_A, _days(-5), confirmed=False)  # not a failure
    # Threshold baseline caught B's failure two days ahead.
    db.add(Alert(equipment_id=EQ_B, status="RESOLVED", created_at=_days(-52)))
    db.commit()
    version = db.get(ModelVersion, vid)
    report = model_ops.evaluate_version(db, version, now=NOW)
    db.close()

    m = report["model"]
    assert (
        m["warnings"],
        m["true_positive"],
        m["false_positive"],
        m["pending"],
    ) == (
        4,
        1,
        2,
        1,
    )
    assert m["precision"] == pytest.approx(1 / 3, abs=1e-3)
    assert (m["failures"], m["failures_detected"], m["recall"]) == (2, 1, 0.5)
    assert m["median_lead_hours"] == 72.0

    b = report["threshold_alerts"]
    assert b["true_positive"] == 1 and b["failures_detected"] == 1
    assert b["median_lead_hours"] == 48.0


def test_evaluation_endpoint_is_admin_only(client: TestClient, as_role, store):
    vid = _version(store)
    as_role("PlantManager")
    assert client.get(f"/v1/models/{vid}/evaluation").status_code == 403
    as_role("Admin")
    resp = client.get(f"/v1/models/{vid}/evaluation?horizon_days=7")
    assert resp.status_code == 200
    assert resp.json()["model"]["warnings"] == 0


# Drift -------------------------------------------------------------------


def test_psi_is_zero_for_identical_and_large_for_shifted() -> None:
    rng = np.random.default_rng(1)
    ref = build_reference(_features(rng, 2000), rng.uniform(0, 1, 2000))
    same = _features(np.random.default_rng(2), 2000)["air_temp_k"].tolist()
    shifted = _features(np.random.default_rng(3), 2000, 6)[
        "air_temp_k"
    ].tolist()
    assert model_ops.psi(ref["features"]["air_temp_k"], same) < 0.1
    assert model_ops.psi(ref["features"]["air_temp_k"], shifted) > 0.25


@pytest.mark.parametrize(
    ("shift", "expected"), [(0.0, "stable"), (6.0, "significant")]
)
def test_drift_report(store, shift, expected) -> None:
    rng = np.random.default_rng(4)
    ref = build_reference(_features(rng, 3000), rng.uniform(0, 0.3, 3000))
    vid = _version(store, reference=ref)
    db = SessionLocal()
    recent = _features(np.random.default_rng(5), 1000, shift)
    for i, row in recent.iterrows():
        _score(
            db,
            vid,
            EQ_A,
            _days(-1) + timedelta(minutes=int(i)),
            False,
            features=row.to_dict(),
            score=float(np.random.default_rng(int(i)).uniform(0, 0.3)),
        )
    db.commit()
    report = model_ops.drift_version(db, db.get(ModelVersion, vid), now=NOW)
    db.close()
    assert report["status"] == expected
    level = report["features"]["air_temp_k"]["level"]
    assert level == ("stable" if shift == 0 else "significant")


def test_drift_needs_reference_and_samples(store) -> None:
    vid = _version(store)
    db = SessionLocal()
    version = db.get(ModelVersion, vid)
    assert (
        model_ops.drift_version(db, version, now=NOW)["status"]
        == "no_reference"
    )
    version.metrics = {
        "reference": build_reference(
            _features(np.random.default_rng(0), 100), np.zeros(100)
        )
    }
    db.commit()
    _score(db, vid, EQ_A, _days(-1), False)
    db.commit()
    report = model_ops.drift_version(db, version, now=NOW)
    db.close()
    assert report["status"] == "insufficient_data"


# Retraining on client labels ----------------------------------------------


@pytest.fixture
def labelled_history(store):
    """30 machines scored every 10 days for 300 days. A failure follows two
    days after any score with air temperature above 301.5 K, a pattern the
    rule-based champion cannot see."""
    vid = _version(store, stage="active")
    rng = np.random.default_rng(7)
    db = SessionLocal()
    ids = []
    for i in range(30):
        e = Equipment(
            equipment_id=f"M-{i:03d}",
            name=f"Mill {i}",
            location="Plant 2",
            type="Mill",
            criticality=3,
            asset_class="ai4i_milling",
        )
        db.add(e)
        db.flush()
        ids.append(e.id)
    feats = _features(rng, 30 * 30)
    k = 0
    for step in range(30):
        for equipment_id in ids:
            at = _days(-305 + step * 10)
            row = feats.iloc[k].to_dict()
            k += 1
            _score(db, vid, equipment_id, at, False, features=row)
            if row["air_temp_k"] > 301.5:
                _failure(db, equipment_id, at + timedelta(days=2))
    db.commit()
    db.close()
    return vid


def test_retrain_writes_challenger_that_beats_champion(
    store, labelled_history, tmp_path
) -> None:
    db = SessionLocal()
    code, report = retrain_client.retrain(
        db,
        asset_class="ai4i_milling",
        version="client-v1",
        min_failures=30,
        out_dir=tmp_path / "artifacts",
        now=NOW,
    )
    db.close()
    assert code == 0, report
    assert report["decision"] == "challenger_better"
    comp = report["comparison"]
    assert comp["challenger"]["pr_auc"] > comp["champion"]["pr_auc"] + 0.2
    assert comp["champion"]["version"] == "rules-v1"
    bundle = joblib.load(tmp_path / "artifacts" / "client-v1" / "model.joblib")
    assert (
        bundle["asset_class"] == "ai4i_milling"
        and bundle["features"] == FEATURES
    )
    assert "reference" in report


def test_retrain_keeps_champion_when_not_better_by_margin(
    store, labelled_history, tmp_path
) -> None:
    db = SessionLocal()
    code, report = retrain_client.retrain(
        db,
        asset_class="ai4i_milling",
        version="client-v2",
        margin=1.0,  # impossible to clear
        out_dir=tmp_path / "artifacts",
        now=NOW,
    )
    db.close()
    assert code == retrain_client.CHAMPION_KEPT
    assert not (tmp_path / "artifacts" / "client-v2").exists()


def test_retrain_waits_for_enough_confirmed_failures(
    store, labelled_history
) -> None:
    db = SessionLocal()
    code, report = retrain_client.retrain(
        db,
        asset_class="ai4i_milling",
        version="client-v3",
        min_failures=10_000,
        now=NOW,
    )
    db.close()
    assert code == retrain_client.INSUFFICIENT_LABELS
    assert report["decision"] == "insufficient_labels"


def test_dataset_drops_rows_whose_outcome_is_not_yet_known(
    store, labelled_history
) -> None:
    db = SessionLocal()
    df, _ = retrain_client.build_dataset(db, "ai4i_milling", 7, NOW)
    db.close()
    assert (df["scored_at"] + timedelta(days=7) <= NOW).all()
    assert 0.1 < df["label"].mean() < 0.4
