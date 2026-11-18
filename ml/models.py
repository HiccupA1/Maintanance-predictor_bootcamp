"""Candidate models, including a rule baseline any ML model must beat."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.config import SEED

# Overstrain limits by product type, as a maintenance engineer would set them
# from the equipment specification.
STRAIN_LIMIT = {"type_L": 11_000.0, "type_M": 12_000.0, "type_H": 13_000.0}


class RuleBaseline(BaseEstimator, ClassifierMixin):
    """Fixed engineering thresholds with no learned parameters.

    Flags: tool wear near end of life, power outside its normal band,
    overstrain over the type limit, and poor heat dissipation at low speed.
    The score is the number of rules tripped (0-4), scaled to [0, 1].
    """

    def fit(self, X: pd.DataFrame, y=None):  # noqa: N803
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:  # noqa: N803
        limit = sum(X[col] * value for col, value in STRAIN_LIMIT.items())
        rules = [
            X["tool_wear_min"] >= 200,
            (X["power_w"] < 3_500) | (X["power_w"] > 9_000),
            X["strain_nm_min"] > limit,
            (X["temp_diff_k"] < 8.6) & (X["rotational_speed_rpm"] < 1_380),
        ]
        score = np.sum(np.column_stack(rules), axis=1) / len(rules)
        return np.column_stack([1 - score, score])

    def predict(self, X: pd.DataFrame) -> np.ndarray:  # noqa: N803
        return (self.predict_proba(X)[:, 1] > 0).astype(int)


def candidates() -> dict[str, BaseEstimator]:
    """Models compared on validation. Learned models are probability-calibrated."""
    logistic = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=2_000),
    )
    boosting = HistGradientBoostingClassifier(
        class_weight="balanced",
        learning_rate=0.05,
        max_iter=400,
        early_stopping=True,
        random_state=SEED,
    )
    return {
        "rule_baseline": RuleBaseline(),
        "logistic_regression": CalibratedClassifierCV(
            logistic, method="sigmoid", cv=5
        ),
        "hist_gradient_boosting": CalibratedClassifierCV(
            boosting, method="isotonic", cv=5
        ),
    }
