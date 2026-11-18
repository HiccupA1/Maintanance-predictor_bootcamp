"""Reference distributions saved with a model, for drift monitoring (WP5).

For each feature, and for the model score, we store interior bin edges (the
training deciles) and the share of training rows in each bin. Production
values are later binned against the same edges and compared using the
Population Stability Index (``app.services.model_ops.psi``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def histogram(values: np.ndarray, bins: int = 10) -> dict:
    """Quantile-binned reference histogram: edges plus proportions."""
    values = np.asarray(values, dtype=float)
    qs = np.linspace(0, 1, bins + 1)[1:-1]
    edges = np.unique(np.quantile(values, qs))
    # Bin i holds values in (edges[i-1], edges[i]], matching bisect_left.
    idx = np.searchsorted(edges, values, side="left")
    counts = np.bincount(idx, minlength=len(edges) + 1)
    return {
        "edges": [round(float(e), 6) for e in edges],
        "proportions": [round(float(c) / len(values), 6) for c in counts],
    }


def build_reference(X: pd.DataFrame, scores: np.ndarray) -> dict:  # noqa: N803
    """Reference for every feature column plus the score distribution."""
    return {
        "features": {col: histogram(X[col].to_numpy()) for col in X.columns},
        "score": histogram(scores),
        "rows": int(len(X)),
    }
