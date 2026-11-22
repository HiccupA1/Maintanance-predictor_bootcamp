# ML Model Operations

These are the lifecycle rules for the failure-risk models (ADR-0006, ADR-0007).
Every version goes **train → register (shadow) → evaluate → activate**, and is
eventually **retired**.

## 1. Train
```bash
pip install -e ".[ml]"
python -m ml.pipelines.train_ai4i --version ai4i-v1
```
Review `ml/artifacts/ai4i-v1/model_card.md`. Publish the card in
`ml/model_cards/` through a PR.

## 2. Register (always shadow)
```bash
# DATABASE_URL and MODEL_STORE_DIR point at the target environment
python -m ml.scripts.register_model ml/artifacts/ai4i-v1
```
This copies the artifact into `MODEL_STORE_DIR` and records its SHA-256,
threshold, feature list and metrics in `model_versions`. The API refuses to
load any artifact whose hash does not match. Joblib files can execute code
when loaded, so never copy artifacts into the store by hand.

## 3. Configure equipment for scoring
- **Equipment:** set `asset_class`, for example `ai4i_milling`, which must match
  the model's asset class.
- **Parameters:** set `feature_key` on each one that feeds the model. Every key
  in `app/core/model_inputs.py` must be mapped: `product_type` (a reading of
  L, M or H), `air_temp_k`, `process_temp_k`, `rotational_speed_rpm`,
  `torque_nm` and `tool_wear_min`. Units must match the key names.

Equipment is scored each time a reading is saved. If any mapped input has no
reading, or a reading is not numeric, the equipment is **not scorable**:
nothing is imputed and nothing is stored.

## 4. Shadow evaluation (Admin → Models, or `GET /v1/models/{id}/evaluation`)
Shadow scores are stored in `risk_scores` and visible to Admins on the
equipment page. They never raise alerts. The evaluation compares the model's
warnings, and the existing threshold alerts on the same machines, against
**confirmed failures**: work orders closed with `failure_confirmed = true`,
timed at when the work order was raised.

| Metric | Meaning |
|---|---|
| Precision | Share of warning episodes followed by a confirmed failure within the horizon (default 7 days). Consecutive flagged scores count as one episode. Episodes whose horizon has not yet passed are *pending* and excluded. |
| Recall | Share of confirmed failures that had a warning in the horizon before them. |
| Median lead | How far ahead of the failure the first warning came. |

**Promotion criteria**, to be agreed with the client and recorded at sign-off:
- enough confirmed failures in the window to be meaningful (at least 10 is a
  sensible minimum);
- the model beats threshold alerts on recall at an acceptable precision, or
  gives materially more lead time;
- drift is not `significant`.

## 4a. Drift (`GET /v1/models/{id}/drift`)
Live inputs and scores are compared with the training reference saved in the
model's metrics, using the Population Stability Index:

| PSI | Level |
|---|---|
| below 0.10 | stable |
| 0.10 to 0.25 | moderate: investigate |
| 0.25 or more | significant: the model is seeing data unlike its training data |

Below 30 recent scores, the result is reported as `insufficient_data`.
Versions registered before WP5 have no reference, and report `no_reference`
until they are retrained.

Scheduled check: `python -m ml.scripts.monitor` prints both reports for every
shadow and active version, and **exits 2 on significant drift**. Run it daily
from the platform scheduler, with the production `DATABASE_URL` held in the
secret store, and alert on a non-zero exit.

## 4b. Retraining on the client's own labels
```bash
python -m ml.pipelines.retrain_client --asset-class ai4i_milling --version client-v1
```
- **Labels:** each stored score, which carries the exact features used at the
  time, is labelled by whether a confirmed failure followed within the
  horizon. Scores whose horizon has not yet passed are dropped.
- **Gate:** training needs at least `--min-failures` (default 30) confirmed
  failures (ADR-0006). Otherwise it exits 3.
- **Split by time:** oldest 60% for training, the next 15% to choose the
  threshold, and the newest 25% as holdout.
- **Challenger vs champion:** the challenger is written out only if it beats
  the champion (the active version, otherwise the newest shadow) on holdout
  PR-AUC by `--margin`. Otherwise it exits 4 and nothing is written.
- **Next:** a written challenger is registered in **shadow** (step 2) and
  goes through steps 4 and 5 like any other version. Nothing is promoted
  automatically.

## 5. Activate, roll back, retire (Admin)
`POST /v1/models/{id}/stage` with `{"stage": "active"}`:
- Before activating, the artifact is verified to load.
- The currently active version for the same asset class is retired
  automatically.
- Who made the change, and when, is recorded on the version.

| Action | How |
|---|---|
| **Roll back** | Activate a version that is still in shadow, or set the bad version to `shadow` (this stops alerts immediately). Retired versions cannot be reinstated, so re-register the artifact as a new version instead. |
| **Kill switch** | Set `SCORING_ENABLED=false` and restart the API. Readings and threshold alerts are unaffected. |

Open `MODEL` alerts stay open after a rollback and are worked like any other
alert. Close them with an accurate `failure_confirmed` value: that label is
what retraining learns from (WP5).

## Runtime notes
- The API needs the `ml` extra installed to score. Without it, scoring logs a
  warning and is skipped.
- Scoring currently runs in the request that saves a reading, which is fine at
  manual-entry volumes. The telemetry worker (WP2) calls the same
  `score_equipment` function.
- `MODEL_STORE_DIR` is a directory for now. The Supabase Storage adapter
  (ADR-0007) will replace `model_registry._resolve`.
