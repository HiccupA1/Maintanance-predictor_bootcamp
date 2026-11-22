# ML: failure-risk models (WP3)

The strategy is set out in ADR-0006 (anomaly detection, a bootstrap
supervised model, and a label feedback loop). This package holds the
bootstrap supervised model, trained on the public AI4I 2020 dataset.

```bash
pip install -e ".[ml]"
python -m ml.pipelines.train_ai4i --version ai4i-v1   # about 1 minute
```

This writes `ml/artifacts/<version>/` (`model.joblib`, `metrics.json`,
`model_card.md`), which is git-ignored. Published model cards are kept in
`ml/model_cards/`.

| Module | Purpose |
|---|---|
| `data/ai4i.py` | Pinned download (SHA-256 checked), schema validation |
| `features/ai4i.py` | Feature construction **shared with the scoring worker** (no train/serve skew); leakage guard |
| `models.py` | Engineering rule baseline, calibrated logistic regression, calibrated gradient boosting |
| `evaluation.py` | Threshold selection against a recall floor; PR-AUC, precision, recall, F1, cost; operating-point table |
| `pipelines/train_ai4i.py` | Train → select on validation → score test once → write artifacts |

## Current result (`ai4i-v1`, held-out test)

Gradient boosting has PR-AUC **0.867** (rule baseline: 0.482). At the
placeholder recall floor of 0.90, precision is 0.36 and recall 0.93. The full
details, the operating-point trade-off and the limitations are in
`model_cards/ai4i-v1.md`.

**Read the limitations before quoting any number.** AI4I is synthetic and its
labels come from rules, so these metrics do not estimate field performance.
Real performance is established in shadow mode against the client's
confirmed failures (WP4/WP5).

## Tests
- `tests/ml/test_pipeline.py` runs offline in CI. It covers the leakage
  guard, feature physics, refusing to impute missing inputs, schema
  validation, threshold selection, and the model contract (probabilities in
  [0, 1]).
- The golden test (`ML_GOLDEN=1 pytest -m golden tests/ml`) retrains on the
  real data and checks the model-card metrics reproduce. It runs in CI
  as a non-blocking job.
