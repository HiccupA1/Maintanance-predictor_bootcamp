"""Train and evaluate the bootstrap failure-risk model on AI4I 2020.

    python -m ml.pipelines.train_ai4i [--version ai4i-v1]

Protocol:
1. Pinned, checksum-verified data, with schema validation.
2. Stratified split into train, validation and test (fixed seed).
3. Every candidate is fit on train and compared on validation (PR-AUC).
4. The operating threshold is chosen on validation against the recall floor.
5. The selected model is scored on the test set once. Test results are
   reported, never used for any choice.

Writes ``ml/artifacts/<version>/`` (model.joblib, metrics.json,
model_card.md), which is git-ignored. Promotion to the registry is a
separate step (WP4).
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split

from ml.config import (
    ARTIFACTS_DIR,
    COST_FALSE_NEGATIVE,
    COST_FALSE_POSITIVE,
    RECALL_FLOOR,
    SEED,
    TEST_FRACTION,
    VAL_FRACTION,
)
from ml.data import ai4i
from ml.evaluation import choose_threshold, evaluate, tradeoff
from ml.features.ai4i import FEATURES, build_features, from_ai4i
from ml.model_card import render_model_card
from ml.models import candidates
from ml.reference import build_reference


def split(X, y):  # noqa: N803
    X_rest, X_test, y_rest, y_test = train_test_split(  # noqa: N806
        X, y, test_size=TEST_FRACTION, stratify=y, random_state=SEED
    )
    X_train, X_val, y_train, y_val = train_test_split(  # noqa: N806
        X_rest,
        y_rest,
        test_size=VAL_FRACTION / (1 - TEST_FRACTION),
        stratify=y_rest,
        random_state=SEED,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def run(version: str) -> dict:
    df = ai4i.load()
    X = build_features(from_ai4i(df))  # noqa: N806
    y = df[ai4i.TARGET].to_numpy()
    X_train, X_val, X_test, y_train, y_val, y_test = split(X, y)  # noqa: N806

    validation: dict[str, dict] = {}
    fitted = {}
    for name, model in candidates().items():
        model.fit(X_train, y_train)
        scores = model.predict_proba(X_val)[:, 1]
        threshold, rule = choose_threshold(y_val, scores, RECALL_FLOOR)
        validation[name] = {**evaluate(y_val, scores, threshold), "rule": rule}
        fitted[name] = model

    learned = {k: v for k, v in validation.items() if k != "rule_baseline"}
    selected = max(learned, key=lambda k: learned[k]["pr_auc"])
    model = fitted[selected]
    threshold = validation[selected]["threshold"]
    operating_points = tradeoff(y_val, model.predict_proba(X_val)[:, 1])
    # Drift baseline (WP5): training features and training-set scores.
    reference = build_reference(X_train, model.predict_proba(X_train)[:, 1])

    # The only use of the test set.
    test = {
        name: evaluate(
            y_test,
            fitted[name].predict_proba(X_test)[:, 1],
            validation[name]["threshold"],
        )
        for name in (selected, "rule_baseline")
    }

    metrics = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": {
            "name": "AI4I 2020 Predictive Maintenance (UCI 601)",
            "sha256": ai4i.CSV_SHA256,
            "rows": int(len(df)),
            "positive_rate": round(float(y.mean()), 4),
            "split": {
                "train": int(len(y_train)),
                "validation": int(len(y_val)),
                "test": int(len(y_test)),
            },
        },
        "protocol": {
            "seed": SEED,
            "selection": "highest validation PR-AUC among learned models",
            "recall_floor": RECALL_FLOOR,
            "cost_false_negative": COST_FALSE_NEGATIVE,
            "cost_false_positive": COST_FALSE_POSITIVE,
        },
        "features": FEATURES,
        "selected_model": selected,
        "validation": validation,
        "operating_points": operating_points,
        "test": test,
        "reference": reference,
        "environment": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
    }

    out = ARTIFACTS_DIR / version
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "threshold": threshold,
            "version": version,
            "kind": "failure_risk",
            "asset_class": "ai4i_milling",
        },
        out / "model.joblib",
    )
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (out / "model_card.md").write_text(
        render_model_card(metrics), encoding="utf-8"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="ai4i-v1")
    metrics = run(parser.parse_args().version)
    sel = metrics["selected_model"]
    print(f"selected: {sel}")
    for name, m in metrics["test"].items():
        print(
            f"test {name:24s} PR-AUC={m['pr_auc']:.3f} "
            f"precision={m['precision']:.3f} recall={m['recall']:.3f} "
            f"F1={m['f1']:.3f} cost/1000={m['cost_per_1000']}"
        )


if __name__ == "__main__":
    main()
