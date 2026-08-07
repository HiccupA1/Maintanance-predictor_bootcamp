# Schema Diff (Live Supabase DB → ORM)

This diff treats the *live database* as the source of truth.

## Table `alerts`
### Column mismatches
- `breach_timestamp` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `created_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `max_threshold` type ORM `FLOAT` != LIVE `FLOAT8`
- `min_threshold` type ORM `FLOAT` != LIVE `FLOAT8`

## Table `equipment`
### Column mismatches
- `created_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `last_service_date` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `updated_at` type ORM `DATETIME` != LIVE `TIMESTAMP`

## Table `parameters`
### Column mismatches
- `created_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `max_threshold` type ORM `FLOAT` != LIVE `FLOAT8`
- `min_threshold` type ORM `FLOAT` != LIVE `FLOAT8`
- `updated_at` type ORM `DATETIME` != LIVE `TIMESTAMP`

## Table `readings`
### Column mismatches
- `modified_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `timestamp` type ORM `DATETIME` != LIVE `TIMESTAMP`

## Table `user_profiles`
### Column mismatches
- `created_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `updated_at` type ORM `DATETIME` != LIVE `TIMESTAMP`

## Table `work_orders`
### Column mismatches
- `created_at` type ORM `DATETIME` != LIVE `TIMESTAMP`
- `updated_at` type ORM `DATETIME` != LIVE `TIMESTAMP`

