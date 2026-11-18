# Model card: ai4i-v1 (bootstrap failure risk)

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
- AI4I 2020 Predictive Maintenance (UCI 601), SHA-256 `dc6630cd9b1f0f85…`, 10,000 rows, failure
  rate 3.4%.
- Stratified split: train 6,000 / validation
  2,000 / test 2,000 (seed
  42).
- **The dataset is synthetic.** Its failure labels are generated from fixed
  rules on these same variables (tool wear, heat dissipation, power,
  overstrain), plus a small random component. High scores here show that the
  model recovers those rules. They are **not** an estimate of performance on
  real equipment.

## Method
- Features (shared with serving): `air_temp_k`, `process_temp_k`, `rotational_speed_rpm`, `torque_nm`, `tool_wear_min`, `temp_diff_k`, `power_w`, `strain_nm_min`, `type_L`, `type_M`, `type_H`.
  Identifiers and the per-mode failure flags are excluded (leakage test).
- Candidates: an engineering rule baseline, calibrated logistic regression,
  and calibrated histogram gradient boosting (both class-weighted).
- Selection: highest validation PR-AUC among learned models.
- Operating threshold, chosen on validation: the most precise threshold with
  recall >= 0.9. The recall floor is a placeholder until
  the client agrees one.
- Cost assumes a missed failure costs 10x a
  false alarm.

## Results

**Selected model:** `hist_gradient_boosting`, threshold 0.038111.

### Validation (used for all choices)
| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 | TP / FP / FN / TN | Cost per 1,000 |
|---|---|---|---|---|---|---|---|
| rule_baseline | 0.546 | 0.968 | 0.321 | 0.985 | 0.484 | 67 / 142 / 1 / 1790 | 76.0 |
| logistic_regression | 0.437 | 0.920 | 0.105 | 0.912 | 0.188 | 62 / 528 / 6 / 1404 | 294.0 |
| hist_gradient_boosting | 0.798 | 0.983 | 0.328 | 0.912 | 0.482 | 62 / 127 / 6 / 1805 | 93.5 |

### Choosing the operating point (validation, selected model)
The client chooses the recall floor. Catching more failures costs more
false alarms:

| Recall floor | Precision | Recall | False alarms per real failure |
|---|---|---|---|
| 0.95 | 0.277 | 0.956 | 2.62 |
| 0.90 | 0.328 | 0.912 | 2.05 |
| 0.85 | 0.374 | 0.853 | 1.67 |
| 0.80 | 0.539 | 0.809 | 0.85 |
| 0.75 | 0.864 | 0.750 | 0.16 |
| 0.70 | 0.864 | 0.750 | 0.16 |

### Test (held out, evaluated once)
| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 | TP / FP / FN / TN | Cost per 1,000 |
|---|---|---|---|---|---|---|---|
| hist_gradient_boosting | 0.867 | 0.972 | 0.360 | 0.926 | 0.518 | 63 / 112 / 5 / 1820 | 81.0 |
| rule_baseline | 0.482 | 0.957 | 0.307 | 0.971 | 0.466 | 66 / 149 / 2 / 1783 | 84.5 |

Accuracy is deliberately not reported. Predicting "no failure" for every row
would score 96.6%.

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
`pip install -e ".[ml]"` then `python -m ml.pipelines.train_ai4i --version ai4i-v1`.
Environment: Python 3.12.10, scikit-learn
1.9.1, NumPy 2.5.5.
