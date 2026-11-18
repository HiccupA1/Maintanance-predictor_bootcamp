"""Render a model card from a training run's metrics."""

from __future__ import annotations


def _row(name: str, m: dict) -> str:
    c = m["confusion"]
    return (
        f"| {name} | {m['pr_auc']:.3f} | {m['roc_auc']:.3f} | "
        f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
        f"{c['tp']} / {c['fp']} / {c['fn']} / {c['tn']} | {m['cost_per_1000']} |"
    )


def render_model_card(metrics: dict) -> str:
    sel = metrics["selected_model"]
    test = metrics["test"]
    ds = metrics["dataset"]
    proto = metrics["protocol"]
    header = (
        "| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 | "
        "TP / FP / FN / TN | Cost per 1,000 |\n|---|---|---|---|---|---|---|---|"
    )
    val_rows = "\n".join(_row(k, v) for k, v in metrics["validation"].items())
    test_rows = "\n".join(_row(k, v) for k, v in test.items())
    tradeoff_rows = "\n".join(
        f"| {p['recall_floor']:.2f} | {p['precision']:.3f} | {p['recall']:.3f} | "
        f"{p['false_alarms_per_failure']} |"
        for p in metrics["operating_points"]
    )
    return f"""# Model card: {metrics['version']} (bootstrap failure risk)

**Stage on creation:** shadow. Not shown to users until reviewed (ADR-0006).

## Intended use
Ranks machines by short-term risk of failure from process signals: air and
process temperature, rotational speed, torque and tool wear. It is a
**bootstrap** model for asset classes whose sensors map onto these inputs.
It is replaced by models retrained on the client's own confirmed failures
(work-order closure labels) as they accumulate (WP5).

**Not for:** asset classes without these signals, safety-critical shutdown
decisions, or any claim about field accuracy.

## Data
- {ds['name']}, SHA-256 `{ds['sha256'][:16]}…`, {ds['rows']:,} rows, failure
  rate {ds['positive_rate']:.1%}.
- Stratified split: train {ds['split']['train']:,} / validation
  {ds['split']['validation']:,} / test {ds['split']['test']:,} (seed
  {proto['seed']}).
- **The dataset is synthetic.** Its failure labels are generated from fixed
  rules on these same variables (tool wear, heat dissipation, power,
  overstrain), plus a small random component. High scores here show that the
  model recovers those rules. They are **not** an estimate of performance on
  real equipment.

## Method
- Features (shared with serving): {', '.join(f'`{f}`' for f in metrics['features'])}.
  Identifiers and the per-mode failure flags are excluded (leakage test).
- Candidates: an engineering rule baseline, calibrated logistic regression,
  and calibrated histogram gradient boosting (both class-weighted).
- Selection: {proto['selection']}.
- Operating threshold, chosen on validation: the most precise threshold with
  recall >= {proto['recall_floor']}. The recall floor is a placeholder until
  the client agrees one.
- Cost assumes a missed failure costs {proto['cost_false_negative']:g}x a
  false alarm.

## Results

**Selected model:** `{sel}`, threshold {metrics['validation'][sel]['threshold']}.

### Validation (used for all choices)
{header}
{val_rows}

### Choosing the operating point (validation, selected model)
The client chooses the recall floor. Catching more failures costs more
false alarms:

| Recall floor | Precision | Recall | False alarms per real failure |
|---|---|---|---|
{tradeoff_rows}

### Test (held out, evaluated once)
{header}
{test_rows}

Accuracy is deliberately not reported. Predicting "no failure" for every row
would score {1 - ds['positive_rate']:.1%}.

## Limitations and risks
- **Synthetic labels.** See Data. Real-world precision and recall are
  unknown until the model is evaluated in shadow mode against the client's
  confirmed failures.
- **Domain shift.** The sensors, units and operating ranges of the client's
  assets will differ. Only asset classes with an explicit feature mapping
  are scored; incomplete inputs are "not scorable", never imputed.
- **Random failures** (RNF) are by construction unpredictable from these
  features.
- **Rule baseline.** On this data, the fixed engineering rules perform close
  to the learned model. In production the ML must show a measurable gain
  over thresholds before it is promoted from shadow to active.

## Reproduce
`pip install -e ".[ml]"` then `python -m ml.pipelines.train_ai4i --version {metrics['version']}`.
Environment: Python {metrics['environment']['python']}, scikit-learn
{metrics['environment']['scikit_learn']}, NumPy {metrics['environment']['numpy']}.
"""
