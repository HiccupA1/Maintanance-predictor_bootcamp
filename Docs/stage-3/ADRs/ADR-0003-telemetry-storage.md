# ADR-0003 — Telemetry Storage

- **Status:** Proposed (CR-001)
- **Decision:** Store raw telemetry in a native PostgreSQL table that is range-partitioned by
  month on `ts`, in the existing Supabase database.
  - Use a BRIN index on `ts` and a B-tree on `(equipment_id, parameter_id, ts DESC)`.
  - Enforce idempotency with a unique constraint on `(device_id, ingest_id, ts)`. The
    partition key must be part of any unique constraint.
  - Enforce retention by detaching and dropping partitions older than 90 days, scheduled with
    `pg_cron` when available, otherwise by a worker maintenance task.
  - Keep hourly aggregates in a separate, non-partitioned table.

## Context

- Sizing assumption: ≈ 300 points/s sustained (`Docs/stage-9/PRD-addendum.md`, NFR-P2).
  That is about 26 M rows/day, or about 2.3 B rows over 90 days before aggregation.
- Access patterns:
  - Append-only writes.
  - Range reads of the latest window per asset, for scoring and charts.
  - Bulk deletion by age.
- Manual readings stay in the existing `readings` table. Its correction and audit semantics
  (5-minute edit window) do not apply to machine telemetry.

## Alternatives considered

| Option | Why not chosen now |
|---|---|
| TimescaleDB hypertables | Compression and continuous aggregates are strong features, but Supabase has deprecated the extension on newer Postgres versions. That ties the client to an extension whose availability we do not control. It is the first upgrade candidate if it is available on the target project. |
| Dedicated TSDB (InfluxDB, ClickHouse) | Adds a second datastore, its own auth, backups and ops, for a volume Postgres handles. Justified above roughly 10k points/s or for long-horizon analytics. |
| Store telemetry in `readings` | Mixes operator-entered, editable data with immutable machine data. It is also unpartitioned and stores values as text (`app/models/equipment.py`). |

## Consequences

- **Positive:**
  - One database, one backup and auth model.
  - Transactional with the queue (ADR-0004).
  - Retention is an O(1) partition drop rather than a mass `DELETE`.
- **Negative:**
  - No native compression, so storage grows linearly until retention. Partitions need
    creating ahead of time, which needs a maintenance job and a monitoring check.
  - SQLAlchemy and Alembic do not autogenerate partitioned DDL, so migrations use raw SQL.
  - SQLite tests use an unpartitioned equivalent, so partition behaviour is covered by the CI
    Postgres job.
- **Revisit when** sustained ingest exceeds about 5k points/s, or storage cost exceeds an
  agreed budget.
