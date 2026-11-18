# Archived Supabase SQL migrations

**Do not apply these.** They are kept for audit only.

These files built the live Supabase schema with `supabase db push`. They have
been replaced by the Alembic baseline `alembic/versions/0001_baseline.py`,
which reproduces the same schema (ADR-0009). Alembic is now the only tool that
changes the database schema.

The `supabase/migrations/` directory has been removed on purpose, so that neither
`supabase db push` nor the Supabase GitHub integration applies schema changes
outside Alembic.

`20260805000000_domain_schema.sql` has had its personal admin grant redacted
(D16). The original is still in git history.
