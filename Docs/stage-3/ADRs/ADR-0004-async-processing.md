# ADR-0004 — Asynchronous Processing of Telemetry

- **Status:** Proposed (CR-001)
- **Decision:** The ingest API inserts the telemetry rows and enqueues **one** message per
  accepted batch to a Postgres-backed queue (Supabase Queues / `pgmq`), in the **same
  transaction**. It then returns `202 Accepted`.
  - A separate worker process uses the same codebase with a different container entrypoint.
  - The worker reads messages with a visibility timeout. It evaluates thresholds (shared rule
    engine, see below), then scoring, and then deletes the message.
  - A message read more than 5 times moves to a dead-letter queue and raises an ops metric.

## Context

- Today, threshold evaluation runs synchronously inside `create_reading`
  (`app/services/domain.py`). That is fine for operator-entered readings. Telemetry is
  different:
  - Batch writes need predictable API latency (NFR-P4: p95 < 300 ms).
  - Model scoring cost must not sit on the ingest path.
  - Processing must survive worker crashes without data loss (NFR-R1).
- The rule engine must be shared. The threshold logic is extracted from `create_reading`
  into a pure function, `evaluate_thresholds(...)`. Manual readings keep calling it
  synchronously, which preserves today's UX. The worker calls it for telemetry. One
  implementation means one behaviour (CR-001 acceptance criterion 4).

## Alternatives considered

| Option | Why not chosen now |
|---|---|
| Synchronous scoring in the request | Couples API latency to model cost, and loses work on timeout. Fails NFR-P4 and NFR-R1 under load. |
| FastAPI `BackgroundTasks` | Runs in the API process memory, so work is lost on restart and the worker cannot scale independently. |
| Redis Streams / Celery | Adds new infrastructure. The enqueue is not transactional with the telemetry insert, so this needs an outbox pattern to avoid lost or phantom messages. |
| Kafka / managed event bus | Right at much higher volumes or for many consumers. Operationally heavy for a single-consumer, roughly 300 msg/s workload. |

## Consequences

- **Positive:**
  - Exactly-once *effect*: an idempotent insert plus a transactional enqueue, so a message
    exists if and only if its rows were committed.
  - Workers scale horizontally, since pgmq visibility timeouts prevent double processing.
  - No new infrastructure.
- **Negative:**
  - Queue load lands on the primary database. Throughput is bounded by Postgres, so this is
    validated by the WP6 load test.
  - Telemetry alerts are eventually consistent, with p95 < 60 s by NFR-P5.
- **Fallback** if `pgmq` is unavailable on the client's plan: a `telemetry_batches` outbox
  table with `SELECT … FOR UPDATE SKIP LOCKED`. The semantics are the same and no extension is
  needed.
- **Upgrade path:** move the transport to Redis Streams or Kafka behind the same
  `enqueue_batch` / `consume` interface in `app/worker/`.
