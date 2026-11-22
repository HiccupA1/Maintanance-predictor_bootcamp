"""ML pipeline tests. They run offline on synthetic rows, except the
opt-in golden test, which retrains on the real AI4I dataset."""

from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")

from ml.data import ai4i  # noqa: E402
from ml.evaluation import choose_threshold, evaluate, tradeoff  # noqa: E402
from ml.features.ai4i import (  # noqa: E402
    FEATURES,
    FORBIDDEN_INPUTS,
    RAW_INPUTS,
    build_features,
    from_ai4i,
)
from ml.models import RuleBaseline, candidates  # noqa: E402


def _ai4i_like(n: int = 400, seed: int = 0) -> pd.DataFrame:
    """Rows in the AI4I schema, with a label driven by power and strain."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "UDI": np.arange(1, n + 1),
            "Product ID": [f"X{i}" for i in range(n)],
            "Type": rng.choice(["L", "M", "H"], n),
            "Air temperature [K]": rng.normal(300, 2, n),
            "Process temperature [K]": rng.normal(310, 1.5, n),
            "Rotational speed [rpm]": rng.integers(1200, 2800, n),
            "Torque [Nm]": rng.normal(40, 10, n),
            "Tool wear [min]": rng.integers(0, 250, n),
        }
    )
    power = df["Torque [Nm]"] * df["Rotational speed [rpm]"] * 2 * math.pi / 60
    strain = df["Tool wear [min]"] * df["Torque [Nm]"]
    df["Machine failure"] = ((power > 8500) | (strain > 11000)).astype(int)
    for mode in ai4i.MODE_COLUMNS:
        df[mode] = 0
    return df


def test_features_exclude_identifiers_and_label_columns() -> None:
    """Leakage guard: no label component or identifier is a model input."""
    assert not FORBIDDEN_INPUTS & set(FEATURES)
    assert not FORBIDDEN_INPUTS & set(RAW_INPUTS.values()) - {"Type"}
    X = build_features(from_ai4i(_ai4i_like()))  # noqa: N806
    assert list(X.columns) == FEATURES
    assert not FORBIDDEN_INPUTS & set(X.columns)


def test_engineered_features_are_physically_correct() -> None:
    raw = pd.DataFrame(
        {
            "product_type": ["M"],
            "air_temp_k": [300.0],
            "process_temp_k": [310.5],
            "rotational_speed_rpm": [1500],
            "torque_nm": [40.0],
            "tool_wear_min": [100],
        }
    )
    X = build_features(raw).iloc[0]  # noqa: N806
    assert X["temp_diff_k"] == pytest.approx(10.5)
    assert X["power_w"] == pytest.approx(40 * 1500 * 2 * math.pi / 60)
    assert X["strain_nm_min"] == pytest.approx(4000)
    assert (X["type_L"], X["type_M"], X["type_H"]) == (0.0, 1.0, 0.0)


def test_missing_inputs_are_not_imputed() -> None:
    raw = from_ai4i(_ai4i_like(5))
    raw.loc[0, "torque_nm"] = np.nan
    with pytest.raises(ValueError, match="not scorable"):
        build_features(raw)
    with pytest.raises(ValueError, match="missing raw inputs"):
        build_features(raw.drop(columns=["tool_wear_min"]))


def test_validate_rejects_bad_schema() -> None:
    df = _ai4i_like(10)
    ai4i.validate(df)
    with pytest.raises(ValueError, match="missing columns"):
        ai4i.validate(df.drop(columns=["Torque [Nm]"]))
    bad = df.copy()
    bad.loc[0, "Type"] = "Z"
    with pytest.raises(ValueError, match="Type"):
        ai4i.validate(bad)


def test_threshold_meets_recall_floor() -> None:
    y = np.array([0] * 90 + [1] * 10)
    scores = np.linspace(0, 1, 100)
    threshold, rule = choose_threshold(y, scores, recall_floor=0.9)
    assert evaluate(y, scores, threshold)["recall"] >= 0.9
    assert "recall" in rule
    assert [p["recall_floor"] for p in tradeoff(y, scores)][:2] == [0.95, 0.9]


@pytest.mark.parametrize("name", list(candidates()))
def test_model_contract(name: str) -> None:
    """Every candidate: fits, outputs probabilities in [0, 1], one per row."""
    df = _ai4i_like(400)
    X = build_features(from_ai4i(df))  # noqa: N806
    model = candidates()[name].fit(X, df["Machine failure"])
    proba = model.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.all((proba >= 0) & (proba <= 1))
    assert np.allclose(proba.sum(axis=1), 1)


def test_rule_baseline_flags_overstrain() -> None:
    raw = pd.DataFrame(
        {
            "product_type": ["L", "L"],
            "air_temp_k": [300.0, 300.0],
            "process_temp_k": [310.0, 310.0],
            "rotational_speed_rpm": [1500, 1500],
            "torque_nm": [40.0, 60.0],
            "tool_wear_min": [
                10,
                190,
            ],  # strain 400 vs 11,400 (L limit 11,000)
        }
    )
    proba = RuleBaseline().fit(None).predict_proba(build_features(raw))[:, 1]
    assert proba[0] == 0 and proba[1] > 0


@pytest.mark.golden
@pytest.mark.skipif(
    os.environ.get("ML_GOLDEN") != "1",
    reason="set ML_GOLDEN=1 (downloads AI4I)",
)
def test_golden_reproduces_reported_metrics(tmp_path, monkeypatch) -> None:
    """Retraining from scratch reproduces the model-card test metrics."""
    from ml.pipelines import train_ai4i

    monkeypatch.setattr(train_ai4i, "ARTIFACTS_DIR", tmp_path)
    metrics = train_ai4i.run("golden")
    test = metrics["test"][metrics["selected_model"]]
    assert metrics["selected_model"] == "hist_gradient_boosting"
    assert test["pr_auc"] == pytest.approx(0.867, abs=0.01)
    assert test["recall"] >= 0.85
