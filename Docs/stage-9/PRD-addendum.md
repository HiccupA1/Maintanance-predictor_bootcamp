# PRD Addendum A — Telemetry Ingestion and ML-Assisted Failure Risk

Extends `Docs/stage-1/PRD-expanded.md`. It applies once CR-001 is approved. Requirement IDs
continue the existing numbering (FR1–FR10).

## 1. Changes to existing scope

- **Explicit non-goals.** "Automated sensor ingestion" and "machine-learning failure
  prediction" are removed from the non-goals list. RUL estimation, notification channels,
  multi-plant governance and native mobile apps remain non-goals.
- **Authentication.** The NFR sentence "Authentication is not enforced in this development
  stage" is replaced by NFR-S1 to NFR-S3 below. The identity shim (ADR-0002) is allowed only
  when `ENV=dev`.

## 2. Functional requirements

### Devices and ingestion
- **FR11.** Admins can register a device bound to exactly one equipment record. On creation
  or rotation, the system shows the device key once and stores only a hash.
- **FR12.** Admins can rotate a device key, which invalidates the old key immediately, and can
  disable a device. Every device key event is audit-logged with the actor and a timestamp.
- **FR13.** A device submits telemetry batches of 1–500 points, each with a parameter
  reference, a numeric value, a timestamp and a device-unique `ingest_id`. The system
  rejects points for parameters that do not belong to the device's equipment.
- **FR14.** Re-submitting a point with an `ingest_id` already accepted for that device is a
  no-op. The response still reports it as accepted (idempotent).
- **FR15.** Telemetry is evaluated against the same inclusive threshold rules as manual
  readings (FR4–FR6), with the same one-active-alert-per-stream lifecycle.

### Scoring
- **FR16.** For each scorable equipment, the system computes an **anomaly score** per
  parameter and per asset. Equipment is scorable once it has the warm-up history (default
  14 days).
- **FR17.** For equipment whose asset class is enabled for a supervised model, and whose
  parameters map to all of that model's features, the system computes a **failure-risk
  probability** (0–1) and a decision at the model's operating threshold.
- **FR18.** Equipment missing required features is shown as *not scorable*, with the
  missing features listed. Values are never silently imputed.
- **FR19.** Each score records the model version and the input features used.
- **FR20.** Model versions have a stage: `shadow`, `active` or `retired`.
  - In `shadow`, scores are recorded but create no alerts.
  - In `active`, a positive decision creates or updates an alert with source `MODEL`
    (supervised) or `ANOMALY`. The explanation lists the top contributing features.
- **FR21.** Only Admins can change a model version's stage. The change records the approver,
  a timestamp and a justification.

### Product surface
- **FR22.** The equipment list shows the latest risk and anomaly status per equipment. The
  equipment detail page shows score history for a selectable time range.
- **FR23.** Alerts display their source: `THRESHOLD`, `ANOMALY` or `MODEL`.
- **FR24.** Closing a work order raised from an alert requires `failure_confirmed`
  (yes/no). When `yes`, `failure_mode` is also required, chosen from: tool wear, heat
  dissipation, power, overstrain, other.
- **FR25.** Admins can view model versions with their metrics, stage history and drift
  status.

### Model operations
- **FR26.** A daily job computes feature drift (Population Stability Index) and score
  distribution shift for each active or shadow model version. A PSI above 0.25 flags the
  version in the admin view.
- **FR27.** A retraining pipeline builds a labelled dataset from telemetry preceding labelled
  closures. A candidate version may only be promoted if it outperforms the current version
  on a time-based holdout.

## 3. Non-functional requirements

These figures are **assumptions to validate with the client** at CR sign-off. They are
sizing inputs, not measured results.

| ID | Requirement | Proposed target |
|---|---|---|
| NFR-P1 | Fleet size | 500 assets × 6 signals |
| NFR-P2 | Sample rate | 1 sample / 10 s per signal (≈ 300 points/s sustained) |
| NFR-P3 | Burst handling | 3× sustained rate for 10 minutes without data loss |
| NFR-P4 | Ingest API latency | p95 < 300 ms, p99 < 1 s per batch of ≤ 500 points |
| NFR-P5 | Reading-to-alert latency | p95 < 60 s from ingest to alert visible |
| NFR-R1 | Durability | Accepted telemetry is not lost on worker restart or crash |
| NFR-R2 | Availability | 99.5% monthly for the ingest API |
| NFR-D1 | Retention | Raw telemetry 90 days; scores 1 year; hourly aggregates 2 years |
| NFR-S1 | Authentication | All user routes require a valid Supabase JWT outside `ENV=dev` |
| NFR-S2 | Authorisation | Role checks per the PRD role matrix; device keys only grant ingest for their bound equipment |
| NFR-S3 | Secrets | Device keys hashed at rest; no secrets in the repository; platform secret store in staging and prod |
| NFR-O1 | Observability | Metrics exposed for ingest rate, queue depth, worker lag and reading-to-alert latency; correlation IDs on all logs |
| NFR-M1 | Reproducibility | Training pipeline reproduces published metrics from a clean checkout with pinned data checksum and seed |

## 4. Role matrix additions

| Capability | Admin | PlantManager | MaintenanceEngineer | Operator | Device |
|---|---|---|---|---|---|
| Manage devices and keys | ✓ | | | | |
| Submit telemetry | | | | | ✓ (own equipment) |
| View risk and anomaly scores | ✓ | ✓ | ✓ | ✓ | |
| Change model stage | ✓ | | | | |
| Record closure outcome | | | ✓ | | |

## 5. Open questions for the client

1. What are the actual fleet size, signals per asset and sample rates? These replace
   NFR-P1/P2.
2. Which plant protocols are in use (MQTT, OPC-UA, Modbus, historian export), and who
   configures the edge gateway?
3. Which asset classes are expected to have temperature, speed, torque and wear signals?
   This determines where the supervised model can be enabled.
4. What data residency or retention obligations apply? This is open item 8 in
   `Docs/stage-1/clarifying-questions.md`.
5. Which cloud should host the API and worker containers (ADR-0008)?
