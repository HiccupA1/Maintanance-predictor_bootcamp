-- Minimal stand-in for the Supabase-managed objects the migrations and
-- scripts/seed_admin.py depend on. CI uses it to exercise the Supabase-only
-- branches of the migrations on plain Postgres. It is NOT a model of
-- Supabase Auth.
create role anon nologin;
create role authenticated nologin;
grant usage on schema public to anon, authenticated;
-- Like Supabase: new tables in public are granted to the Data API roles.
alter default privileges in schema public
  grant all on tables to anon, authenticated;
create schema auth;
create table auth.users (
  id uuid primary key,
  email text,
  raw_user_meta_data jsonb
);
create function auth.uid() returns uuid
  language sql stable as 'select null::uuid';
