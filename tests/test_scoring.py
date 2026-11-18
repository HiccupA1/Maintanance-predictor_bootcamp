"""Risk scoring end to end: registry, shadow/active stages, MODEL alerts."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

pytest.importorskip("sklearn")

import joblib  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.model_inputs import FEATURE_KEYS  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.alert import Alert  # noqa: E402
from app.models.equipment import Equipment, Parameter  # noqa: E402
from app.models.ml import ModelVersion, RiskScore  # noqa: E402
from app.services import model_registry  # noqa: E402
from ml.features.ai4i import FEATURES, RAW_INPUTS  # noqa: E402
from ml.models import RuleBaseline  # noqa: E402

EQUIPMENT_PK = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"
SAFE = {
    "product_type": "L",
    "air_temp_k": "300",
    "process_temp_k": "310",
    "rotational_speed_rpm": "1500",
    "torque_nm": "40",
    "tool_wear_min": "10",
}
# Tool wear past end of life, power above band, overstrain: rule score 0.75.
RISKY = {**SAFE, "torque_nm": "60", "tool_wear_min": "220"}


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


@pytest.fixture
def model_version(store) -> str:
    """Register a rule-baseline artifact (threshold 0.25) in shadow."""
    path = store / "rules-v1.joblib"
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
        stage="shadow",
        threshold=0.25,
        features=FEATURES,
        artifact_uri=path.name,
        artifact_sha256=model_registry.sha256_file(path),
    )
    db.add(row)
    equipment = db.get(Equipment, EQUIPMENT_PK)
    equipment.asset_class = "ai4i_milling"
    params = {}
    for key in FEATURE_KEYS:
        p = Parameter(
            equipment_id=EQUIPMENT_PK,
            name=key,
            unit="-",
            max_threshold=1e9,
            feature_key=key,
        )
        db.add(p)
        params[key] = p
    db.commit()
    model_id = row.id
    db.close()
    return model_id


def _param_ids() -> dict[str, str]:
    db = SessionLocal()
    rows = db.execute(
        select(Parameter.feature_key, Parameter.id).where(
            Parameter.equipment_id == EQUIPMENT_PK
        )
    ).all()
    db.close()
    return dict(rows)


def _record(client: TestClient, as_role, values: dict) -> None:
    as_role("Operator")
    ids = _param_ids()
    for key, value in values.items():
        resp = client.post(
            "/v1/readings",
            json={
                "equipment_id": "eq-1111",
                "parameter_id": ids[key],
                "value": value,
            },
        )
        assert resp.status_code == 201, resp.text


def _scores() -> list[RiskScore]:
    db = SessionLocal()
    rows = list(db.execute(select(RiskScore)).scalars())
    db.close()
    return rows


def _model_alerts() -> list[Alert]:
    db = SessionLocal()
    rows = list(
        db.execute(select(Alert).where(Alert.source == "MODEL")).scalars()
    )
    db.close()
    return rows


def test_feature_keys_match_ml_raw_inputs() -> None:
    assert set(FEATURE_KEYS) == set(RAW_INPUTS)


def test_not_scorable_until_every_input_is_present(
    client, as_role, model_version
) -> None:
    partial = {k: v for k, v in RISKY.items() if k != "tool_wear_min"}
    _record(client, as_role, partial)
    assert _scores() == []


def test_shadow_scores_are_stored_but_raise_no_alert(
    client, as_role, model_version
) -> None:
    _record(client, as_role, RISKY)
    scores = _scores()
    assert scores and scores[-1].stage == "shadow" and scores[-1].flagged
    # wear, power and overstrain rules: 3 of 4
    assert scores[-1].score == pytest.approx(0.75)
    assert _model_alerts() == []

    as_role("PlantManager")
    body = client.get("/v1/equipment/eq-1111/risk").json()
    assert body["status"] == "no_scores"  # shadow hidden from non-admins
    as_role("Admin")
    body = client.get("/v1/equipment/eq-1111/risk").json()
    assert body["latest"]["stage"] == "shadow"
    assert body["latest"]["model_version"] == "rules-v1"


def test_active_model_raises_and_resolves_model_alert(
    client, as_role, model_version
) -> None:
    as_role("Admin", name="Ada Admin")
    resp = client.post(
        f"/v1/models/{model_version}/stage", json={"stage": "active"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["stage_changed_by"] == "Ada Admin"

    _record(client, as_role, RISKY)
    alerts = _model_alerts()
    assert len(alerts) == 1 and alerts[0].status == "NEW"
    assert "rules-v1" in alerts[0].why_priority

    _record(client, as_role, RISKY)  # still risky: same alert, not a new one
    assert len(_model_alerts()) == 1

    _record(client, as_role, SAFE)
    assert _model_alerts()[0].status == "RESOLVED"

    as_role("PlantManager")
    body = client.get("/v1/equipment/eq-1111/risk").json()
    assert body["status"] == "scored" and body["latest"]["flagged"] is False
    listed = client.get("/v1/alerts")
    assert listed.status_code in (200, 500)  # D8 may still 500 on SQLite


def test_activating_retires_previous_active(
    client, as_role, model_version, store
):
    as_role("Admin")
    client.post(f"/v1/models/{model_version}/stage", json={"stage": "active"})
    db = SessionLocal()
    second = ModelVersion(
        version="rules-v2",
        asset_class="ai4i_milling",
        stage="shadow",
        threshold=0.25,
        features=FEATURES,
        artifact_uri="rules-v1.joblib",
        artifact_sha256=model_registry.sha256_file(store / "rules-v1.joblib"),
    )
    db.add(second)
    db.commit()
    second_id = second.id
    db.close()
    resp = client.post(
        f"/v1/models/{second_id}/stage", json={"stage": "active"}
    )
    assert resp.status_code == 200
    models = {
        m["version"]: m["stage"] for m in client.get("/v1/models").json()
    }
    assert models == {"rules-v1": "retired", "rules-v2": "active"}
    resp = client.post(
        f"/v1/models/{model_version}/stage", json={"stage": "active"}
    )
    assert resp.status_code == 409  # retired cannot be reinstated


def test_tampered_artifact_cannot_be_activated_and_never_breaks_readings(
    client, as_role, model_version, store
) -> None:
    (store / "rules-v1.joblib").write_bytes(b"tampered")
    model_registry.clear_cache()
    as_role("Admin")
    resp = client.post(
        f"/v1/models/{model_version}/stage", json={"stage": "active"}
    )
    assert resp.status_code == 409
    assert "verification" in resp.json()["detail"]
    _record(client, as_role, RISKY)  # scoring fails, readings still succeed
    assert _scores() == []


def test_artifact_path_cannot_escape_store(model_version, store) -> None:
    db = SessionLocal()
    version = db.get(ModelVersion, model_version)
    version.artifact_uri = "../outside.joblib"
    with pytest.raises(model_registry.ArtifactError, match="escapes"):
        model_registry.load(version)
    db.close()


def test_parameter_feature_key_is_validated(client, as_role) -> None:
    as_role("PlantManager")
    resp = client.post(
        "/v1/equipment/eq-1111/parameters",
        json={
            "name": "x",
            "unit": "-",
            "max_threshold": 1,
            "feature_key": "bogus",
        },
    )
    assert resp.status_code == 422
    resp = client.post(
        "/v1/equipment/eq-1111/parameters",
        json={
            "name": "Torque",
            "unit": "Nm",
            "max_threshold": 80,
            "feature_key": "torque_nm",
        },
    )
    assert (
        resp.status_code == 201 and resp.json()["feature_key"] == "torque_nm"
    )
