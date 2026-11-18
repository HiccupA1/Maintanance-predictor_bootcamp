"""Metrics and operating-threshold selection.

Accuracy is never reported as a headline: with about 3.4% positives, a model
that always predicts "no failure" scores about 96.6%.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.config import COST_FALSE_NEGATIVE, COST_FALSE_POSITIVE


def choose_threshold(
    y_true: np.ndarray, scores: np.ndarray, recall_floor: float
) -> tuple[float, str]:
    """Pick the most precise threshold whose recall is >= ``recall_floor``.

    Falls back to the F1-maximising threshold when the floor is unreachable.
    Use on validation data only.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    # precision/recall have one more entry than thresholds.
    precision, recall = precision[:-1], recall[:-1]
    ok = recall >= recall_floor
    if ok.any():
        best = np.flatnonzero(ok)[np.argmax(precision[ok])]
        return (
            float(thresholds[best]),
            f"max precision at recall >= {recall_floor}",
        )
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    return (
        float(thresholds[int(np.argmax(f1))]),
        "max F1 (recall floor unreachable)",
    )


def tradeoff(
    y_true: np.ndarray,
    scores: np.ndarray,
    floors: tuple[float, ...] = (0.95, 0.9, 0.85, 0.8, 0.75, 0.7),
) -> list[dict]:
    """Best precision achievable at each recall floor (validation only).

    This is the table the client uses to choose the operating point.
    """
    rows = []
    for floor in floors:
        threshold, _ = choose_threshold(y_true, scores, floor)
        m = evaluate(y_true, scores, threshold)
        rows.append(
            {
                "recall_floor": floor,
                "threshold": m["threshold"],
                "precision": m["precision"],
                "recall": m["recall"],
                "false_alarms_per_failure": round(
                    m["confusion"]["fp"] / max(m["confusion"]["tp"], 1), 2
                ),
            }
        )
    return rows


def evaluate(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    """Threshold-free and thresholded metrics plus cost per 1,000 units."""
    y_pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n = len(y_true)
    cost = COST_FALSE_NEGATIVE * fn + COST_FALSE_POSITIVE * fp
    return {
        "n": int(n),
        "positives": int(y_true.sum()),
        "pr_auc": round(float(average_precision_score(y_true, scores)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, scores)), 4),
        "threshold": round(float(threshold), 6),
        "precision": round(
            float(precision_score(y_true, y_pred, zero_division=0)), 4
        ),
        "recall": round(
            float(recall_score(y_true, y_pred, zero_division=0)), 4
        ),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "confusion": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "cost_per_1000": round(float(cost / n * 1000), 2),
    }
