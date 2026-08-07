-- Add missing optional context fields to alerts.
-- This aligns the Supabase-managed schema with the backend SQLAlchemy Alert model
-- (issuer_name, machine_details, readings_snapshot).

alter table public.alerts
  add column if not exists issuer_name text;

alter table public.alerts
  add column if not exists machine_details jsonb;

alter table public.alerts
  add column if not exists readings_snapshot jsonb;
