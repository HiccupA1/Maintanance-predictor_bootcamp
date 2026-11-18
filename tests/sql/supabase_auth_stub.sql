-- Minimal stand-in for the Supabase-managed objects the baseline migration
-- and scripts/seed_admin.py depend on. CI uses it to exercise the
-- Supabase-only branch of alembic/versions/0001_baseline.py on plain
-- Postgres. It is NOT a model of Supabase Auth.
create role authenticated nologin;
create schema auth;
create table auth.users (
  id uuid primary key,
  email text,
  raw_user_meta_data jsonb
);
create function auth.uid() returns uuid
  language sql stable as 'select null::uuid';
