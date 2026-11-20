# Performance Report (WP6)

**Date:** 2026-11-20
**Build:** `release/wp6` (PR #13)
**Status:** measured. Every figure below comes from a recorded run, with its
environment stated.

## Scope and targets

WP2 (automated sensor ingestion) was descoped on 2026-11-19, so readings stay
manual. The load profile is therefore people using the app, not machines
streaming data. The CR-001 telemetry target (about 300 messages per second)
no longer applies.

| Target (manual operation) | Value |
|---|---|
| Baseline load (1×) | 25 concurrent active users, each acting every 0.2–0.8 s |
| Stress load (3×) | 75 concurrent users |
| Read endpoints, p95 | < 300 ms |
| Recording a reading, p95 (threshold check included; scoring runs after the response) | < 500 ms |
| Error rate | < 0.1 % |

The 1× figure is an assumption to confirm with the client. 25 people all
acting continuously is a busy plant shift.

## Method

Harness: `tools/loadtest/`.
- `setup.py` generates a signing key and a JWKS file. Requests carry real RS256
  tokens, verified by the production JWT code path. It seeds 50 machines
  (each with the 6 parameters mapped to model inputs), one user per role, and
  registers the trained `ai4i-v1` model in **shadow**, so every reading is
  really scored.
- `run.py` is a closed loop: each virtual user picks a weighted scenario,
  sends it, then waits 0.2–0.8 s.

| Scenario | Share | Role |
|---|---|---|
| `GET /equipment` | 25 % | Plant Manager |
| `POST /readings` (threshold check, then background risk scoring) | 25 % | Operator |
| `GET /equipment/{id}/risk` | 15 % | Maintenance Engineer |
| `GET /alerts` | 15 % | Plant Manager |
| `GET /work-orders?page_size=50` | 10 % | Maintenance Engineer |
| Readings history | 10 % | Operator |

Each run lasts 60 s.

## Results: CI (Linux), the reference measurement

Job `Load test (Linux, Postgres, real model)`, GitHub-hosted `ubuntu-latest`
(4 vCPU). It ran Postgres 17 as a service container and the API with 3
uvicorn workers. The load generator ran on the same runner. The raw JSON is
in the job's `load-test` artifact.

| Load | Requests | Throughput | Errors | p50 | p95 | p99 |
|---|---|---|---|---|---|---|
| 1× (25 users) | 2,807 | 46.2 rps | 0 | 45.5 ms | **51.0 ms** | 132.1 ms |
| 3× (75 users) | 8,122 | 133.7 rps | 0 | 49.8 ms | **101.9 ms** | 189.5 ms |

Per scenario, at 3×:

| Scenario | n | p50 | p95 | p99 |
|---|---|---|---|---|
| `GET /equipment` | 2,007 | 48.8 | 89.0 | 141.8 |
| `POST /readings` | 2,013 | 54.4 | 133.7 | 241.2 |
| `GET /alerts` | 1,229 | 47.8 | 87.3 | 132.1 |
| `GET /equipment/{id}/risk` | 1,240 | 48.8 | 90.1 | 163.3 |
| `GET /work-orders` | 813 | 48.0 | 94.7 | 138.9 |
| Readings history | 820 | 49.2 | 96.9 | 161.8 |

During the run, background scoring wrote 1,998 risk scores. Readings recorded
before all 6 mapped inputs of a machine had values are correctly not scored.

**Verdict:** every target is met at 3× load, with no errors. At 1×, throughput
is limited by the users' own think time (25 users ÷ 0.5 s ≈ 50 rps), not by
the server. Throughput rises almost linearly to 3×.

**Caveat.** Every endpoint, including trivial ones, has a p50 of about 45 ms.
Single-request server times measured directly are 7–25 ms (below), so this
floor is very likely a client-side or TCP loopback artifact (for example
delayed ACK). If anything, the absolute latencies above overstate server time.

## What profiling found, and what changed

The first runs were made on a development laptop (Windows, 12 logical cores).
They surfaced two real problems, which are now fixed:

| Finding | Evidence | Fix |
|---|---|---|
| Risk scoring ran **inside** the reading request: about 119 ms of CPU per reading, 78 ms of it the 5-fold calibrated gradient-boosting predict | in-process profile | Scoring now runs as a background task after the response, with its own DB session (`scoring.score_in_background`) |
| scikit-learn's OpenMP used every core for every prediction, oversubscribing the CPU under concurrency | predict: 79.6 ms with default threads, 51.0 ms with 1 thread | `OMP_NUM_THREADS=1`, set before scikit-learn loads (`app/main.py`, Dockerfile). Scale out with workers or replicas instead |
| The default SQLAlchemy pool (5 + 10, 30 s timeout) turned overload into 30-second stalls instead of visible errors | p99 up to 23 s in laptop runs | `DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=10`, `DB_POOL_TIMEOUT_S=5` |

Single-request latencies (laptop, sequential, local Postgres): `/v1/health`
7 ms; `/v1/health/db` 11 ms; `/v1/me` (JWT plus profile) 17 ms;
`GET /v1/equipment` 25 ms.

**The laptop load numbers are not valid capacity figures and are not
reported.** Even `/v1/health`, which does no work, capped at about 50 rps
with 1 or 4 workers. The load generator competed with the API for the same
machine, and Windows lacks `SO_REUSEPORT`, so uvicorn workers did not share
load. That is why the reference measurement runs on Linux.

## Capacity guidance for deployment

- **Connections:** each worker opens up to `DB_POOL_SIZE + DB_MAX_OVERFLOW`
  = 20. Keep `replicas × workers × 20` under the Supabase pooler's connection
  limit for the client's plan, or lower the pool settings.
- **Scoring cost:** a score costs about 50 ms of single-threaded CPU. At the
  3× rate, 33 readings per second means about 1.7 CPU-seconds per second
  spent scoring. Put 2 vCPU or more behind the API, or move scoring to a
  separate worker if reading volume grows.
- **Cheaper model:** retraining with `CalibratedClassifierCV(ensemble=False)`
  (one model instead of five) would cut scoring CPU by roughly 5×. It needs a
  new model version and shadow evaluation, so it is not done here.

## Not measured

- **Production network, TLS and the Supabase pooler.** Repeat the run on
  staging with the same harness (`tools/loadtest`, pointing `--base` at
  staging and using real staging tokens) before go-live.
- **Long-duration soak, and data volumes beyond the seeded test set.**
  `GET /alerts` and the readings history are **unpaginated**. They will slow
  as history grows, so add pagination before history reaches thousands of
  rows per list.
