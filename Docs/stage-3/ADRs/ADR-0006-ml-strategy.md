# ADR-0006 — ML Strategy Without Client Failure History

- **Status:** Proposed (CR-001)
- **Decision:** Use three complementary signals, rolled out behind shadow mode.
  1. **Threshold rules** (existing) stay the primary, deterministic alert source.
  2. **Label-free anomaly detection**, learned from each asset's *own* telemetry:
     - Univariate: rolling median/MAD robust z-scores per equipment-parameter.
     - Multivariate: an Isolation Forest per asset class on windowed features.
     - It becomes eligible after a 14-day warm-up.
  3. **Supervised failure-risk model**:
     - Bootstrapped on the public AI4I 2020 Predictive Maintenance dataset (UCI).
     - Gradient-boosted trees with calibrated probabilities.
     - Enabled only for asset classes whose parameters map to its features.
  4. **Outcome feedback loop**:
     - Work-order closure records `failure_confirmed` and `failure_mode` (FR24).
     - When an asset class reaches **≥ 30 confirmed failures**, a client-data retraining
       candidate is built.
     - The candidate is promoted only if it beats the current version on a time-based
       holdout.

## Context

- The client has no historical failure data and will not supply any (CR-001 §5). Supervised
  learning on client data is therefore impossible at launch.
- Anomaly detection needs no labels, and it adapts to any asset type.
- AI4I 2020 (10,000 rows, ≈ 3.4% failures) is a well-known benchmark with real labels. Its
  features are air temperature, process temperature, rotational speed, torque, tool wear and
  product variant. It is a milling process, so transfer to the client's assets is **not
  assumed**.

## Evaluation protocol (supervised model)

- Stratified 70/15/15 train/validation/test split with a fixed seed and a pinned dataset
  checksum.
- Model and hyperparameter selection on the validation set only. **The test set is evaluated
  exactly once** per published version.
- Leakage guard: the per-mode failure columns (TWF, HDF, PWF, OSF, RNF) and identifiers are
  excluded. A unit test asserts this.
- Baselines: majority class, the threshold rules, and logistic regression.
- Metrics:
  - Precision, recall, F1, PR-AUC, the confusion matrix, and a cost-weighted error with
    missed failure ≫ false alarm.
  - **Plain accuracy is not reported as a headline metric**, because always predicting "no
    failure" scores ≈ 96.6%.
- The operating threshold is chosen on validation, to meet a recall floor agreed with the
  client (default 0.80).

## Rollout

- New model versions enter the registry as `shadow`. They score and record, but raise no
  alerts.
- Promotion to `active` requires a shadow evaluation report and recorded Admin approval
  (FR21). The minimum shadow period is 4 weeks.
- Rollback is a stage change back to the previous version. It needs no redeploy.

## Alternatives considered

| Option | Why not chosen |
|---|---|
| Synthetic failure data only | Metrics on self-generated data show nothing about real performance. It is used only for integration tests and demos. |
| Remaining-useful-life models (C-MAPSS, LSTMs) | Need run-to-failure histories per asset, which the client does not have. Out of scope. |
| Deep or sequence models (LSTM, autoencoders) | No labelled sequences to justify them, and harder to explain to maintenance staff. Gradient-boosted trees are strong on tabular features and support per-feature explanations. |
| Rules only (no ML) | Valid and safe, but misses multivariate degradation. Anomaly scoring adds this with no labels. |

## Consequences

- **Positive:**
  - Delivers label-free value from day one.
  - Outcome labels accumulate automatically.
  - Every claim about model quality is tied to a stated dataset and protocol.
- **Negative:**
  - Supervised-model value on client assets stays unproven until labels accrue. It must be
    described as advisory until then.
  - Anomaly alerts carry false-positive risk, which shadow mode and per-asset enablement
    contain.
