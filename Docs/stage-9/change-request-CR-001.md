# CR-001 — Telemetry Ingestion and ML-Assisted Failure Risk

- **Status:** Proposed. Awaiting client sign-off.
- **Raised by:** DigitalT3 delivery team
- **Affects:** PRD (`Docs/stage-1/PRD-expanded.md`), architecture (`Docs/stage-3/`), QA plan
  (`Docs/stage-5`, `Docs/stage-7`), release plan (`Docs/stage-8`)
- **Companion documents:** `PRD-addendum.md` (requirements),
  ADR-0003 to ADR-0008 (`Docs/stage-3/ADRs/`)

## 1. Summary

The signed-off MVP excludes automated sensor ingestion and machine-learning failure
prediction (PRD, "Explicit non-goals"). This change request brings both into scope:

1. **Automated telemetry ingestion.** Plant devices or edge gateways push readings to the
   platform without manual entry.
2. **Health scoring.**
   - Label-free anomaly detection on each asset's own telemetry.
   - A supervised failure-risk model for asset classes that match its input features.
3. **Outcome capture.** Work-order closure records whether a failure was confirmed and its
   mode. This is the ground truth for evaluating and retraining models.
4. **Controlled rollout.** Model output runs in *shadow mode* (recorded, not alerted) until
   a documented review promotes it.

## 2. Motivation

- Manual readings are sparse and depend on operator rounds. Breaches between rounds go
  undetected.
- Fixed thresholds only catch a fault once a value is already out of bounds. Trend and
  multivariate scoring can surface degradation earlier.
- Today, closed work orders record no failure outcome, so the client cannot measure whether
  alerts were correct. Outcome capture is valuable even without ML.

## 3. Pre-conditions (must complete before new capability ships)

The current baseline is not release-ready, as shown in `Docs/stage-5/api-readiness-signoff.md`
and `Docs/stage-7/system-qa-signoff.md`. Work package WP1 closes these gaps first:

| Gap | Resolution in WP1 |
|---|---|
| API sign-off NO-GO: P1 on work-order `page_size=200` | Fix plus regression test |
| 7 npm audit findings (1 critical, 5 high) | Upgrade or replace the dependencies until high/critical = 0 |
| Frontend TypeScript, build and test-runner failures | Fix; CI gate |
| Several read/write routes have no authentication guard | Apply role guards per the PRD role matrix, and restrict the dev identity fallback to `ENV=dev` |
| PRD FR9–FR10 (closure with root cause and parts; closure resolves the source alert) are not in the live schema | Implement, and add the outcome-label fields |
| No CI; tests only run against SQLite | GitHub Actions with a Postgres service container; protected `main` |

## 4. Scope

### In scope
- Device registry with per-device credentials (create, rotate, disable), admin only, audited.
- HTTPS batch ingestion API that is idempotent and rate-limited per device.
- Partitioned telemetry store with a defined retention policy.
- Asynchronous processing worker that applies the existing threshold rules to telemetry, then
  scoring.
- Anomaly scoring per asset parameter, plus multivariate scoring per asset class.
- A supervised failure-risk model, bootstrapped on the public AI4I 2020 benchmark dataset.
- A model registry: versions, stages (shadow / active / retired), metrics and checksums.
- Risk views in the UI (equipment list and detail) and alert source labelling.
- Outcome-label capture on work-order closure, a drift monitoring job, and a retraining
  pipeline.
- Edge simulator, used for demos, integration tests and load tests.
- Containerised API and worker deployment, with CI/CD.

### Out of scope (unchanged or deferred)
- On-premise edge gateway installation and plant network or OT integration. The client or
  their integrator configures a gateway against the documented ingest API.
- Native MQTT or OPC-UA brokers in the cloud platform. See ADR-0005 for why these are
  bridged at the edge.
- Multi-plant or multi-tenant governance, native mobile apps, notification channels (email,
  SMS, pager).
- Remaining-useful-life (RUL) estimation.

## 5. Key limitation the client must accept

**The client has no historical failure data, and none will be supplied.** As a result:

- The supervised model is trained on **public benchmark data (AI4I 2020, a milling-process
  dataset)**. Its metrics describe performance **on that benchmark**, not on the client's
  equipment. It is only enabled for asset classes whose sensors map to its features
  (temperature pair, rotational speed, torque, tool/run wear).
- Anomaly detection needs no labels. It learns each asset's normal behaviour from the
  client's own telemetry, after a warm-up period (default 14 days of data). Threshold rules
  remain the primary alert mechanism during warm-up.
- Model accuracy on the client's assets can only be measured once closures carry outcome
  labels. A retraining and re-evaluation milestone is set at ≥ 30 confirmed failures per
  asset class (ADR-0006). Until then, model output must be described as **advisory**.
- No model output will create user-visible alerts until a shadow-mode review (§7) is signed
  off.

## 6. Delivery plan

| WP | Content | Exit criteria |
|---|---|---|
| WP0 | This CR, PRD addendum, ADR-0003 to ADR-0008 | Client sign-off of CR and NFR assumptions |
| WP1 | Baseline hardening (see §3) | CI green; API and system QA re-run with GO; 0 high/critical vulns |
| WP2 | Devices, ingest API, telemetry store, worker, simulator, metrics | Simulator at NFR rate; idempotency and worker-restart tests pass |
| WP3 | ML pipeline, model card, registry promotion | Reproducible metrics from a clean checkout; leakage test passes |
| WP4 | Scoring in the worker, risk API and UI, closure label fields in UI | Shadow → active promotion demonstrated end to end |
| WP5 | Drift monitoring, shadow evaluation report, retraining pipeline | Drift job and retraining run on seeded data |
| WP6 | Load test, security review, release documents | NFRs met or gaps documented; security checklist complete |

Each work package is delivered as one or more pull requests to a protected `main` branch,
with all CI checks required.

## 7. Acceptance criteria

1. Every NFR in `PRD-addendum.md` §3 is met in the WP6 load test at 1× the agreed rate, or
   any gap is documented and accepted.
2. Ingestion is idempotent: re-sending a batch with the same `ingest_id` values creates no
   duplicate telemetry.
3. No telemetry is lost if the worker stops. Queued messages are processed after restart.
4. Telemetry and manual readings produce identical threshold alerts for identical values,
   because one rule engine serves both.
5. The model card publishes held-out benchmark metrics: precision, recall, F1, PR-AUC,
   confusion matrix, and comparison with a threshold baseline. Plain accuracy is not used as
   a headline metric.
6. **Shadow-mode exit:** after at least 4 weeks in shadow, a report compares model and
   anomaly signals against threshold alerts and labelled closures. Promotion to active is
   recorded in the model registry with the approver's identity.
7. Every closure of a work order raised from an alert records `failure_confirmed`.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Benchmark model does not transfer to the client's assets | Poor precision; alert fatigue | Shadow mode; per-asset-class enablement; anomaly detection as a label-free primary signal |
| Too few confirmed failures to ever retrain | Model stays benchmark-only | Outcome capture is mandatory on closure; anomaly path keeps value; document as advisory |
| Telemetry volume exceeds the Postgres design | Ingest latency, storage cost | Partitioning and retention; measured load test; documented upgrade path (ADR-0003, ADR-0004) |
| Device credential leakage | Data poisoning | Hashed keys, rotation, per-device scope, rate limits, audit log |
| Extension availability on the client's Supabase plan (`pgmq`, `pg_cron`) | Design change | Verified in WP2 start; fallbacks documented in ADRs |

## 9. Sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Client product owner | | | |
| DigitalT3 delivery lead | | | |
