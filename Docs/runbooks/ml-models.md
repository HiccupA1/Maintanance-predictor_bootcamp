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

## 4. Shadow evaluation
Shadow scores are stored in `risk_scores` and visible to Admins on the
equipment page. They never raise alerts. Before promoting a version:
- compare flagged shadow scores with what happened (threshold alerts and
  work-order closures with `failure_confirmed`) over an agreed period;
- confirm the precision and recall at the chosen threshold are acceptable to
  the client;
- record the review outcome and sign-off. The WP5 shadow report automates this.

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
