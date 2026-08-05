create extension if not exists "pgcrypto";

create table if not exists public.equipment (
  id uuid primary key default gen_random_uuid(),
  equipment_id text unique not null,
  name text not null,
  location text not null default '',
  type text not null default '',
  criticality integer not null default 1,
  last_service_date timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.parameters (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid not null references public.equipment(id) on delete cascade,
  name text not null,
  unit text not null default '',
  min_threshold double precision,
  max_threshold double precision,
  active boolean not null default true,
  suggested_action text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.readings (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid not null references public.equipment(id) on delete cascade,
  parameter_id uuid not null references public.parameters(id) on delete cascade,
  value text not null,
  timestamp timestamptz not null default now(),
  entered_by text not null default 'dev',
  modified_by text,
  modified_at timestamptz,
  modification_reason text
);

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid references public.equipment(id) on delete set null,
  parameter_id uuid references public.parameters(id) on delete set null,
  priority text not null default 'MEDIUM',
  current_value text,
  breach_timestamp timestamptz,
  min_threshold double precision,
  max_threshold double precision,
  suggested_action text,
  why_priority text,
  status text not null default 'OPEN',
  created_at timestamptz not null default now()
);

create table if not exists public.work_orders (
  id uuid primary key default gen_random_uuid(),
  equipment_id uuid references public.equipment(id) on delete set null,
  title text not null,
  description text,
  status text not null default 'OPEN',
  priority text not null default 'MEDIUM',
  assigned_to text,
  closed_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_profiles (
  id uuid primary key default gen_random_uuid(),
  supabase_user_id uuid unique not null references auth.users(id) on delete cascade,
  email text,
  display_name text,
  role text not null default 'Operator'
    check (role in ('Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.user_profiles'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%Admin%'
      and pg_get_constraintdef(oid) like '%PlantManager%'
      and pg_get_constraintdef(oid) like '%MaintenanceEngineer%'
  ) then
    alter table public.user_profiles
      add constraint user_profiles_role_check
      check (role in ('Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer'));
  end if;
end
$$;

create index if not exists parameters_equipment_id_idx on public.parameters(equipment_id);
create index if not exists readings_parameter_id_idx on public.readings(parameter_id);
create index if not exists readings_timestamp_idx on public.readings(timestamp desc);
create index if not exists alerts_status_idx on public.alerts(status);
create index if not exists work_orders_status_idx on public.work_orders(status);
create index if not exists user_profiles_role_idx on public.user_profiles(role);

alter table public.equipment enable row level security;
alter table public.parameters enable row level security;
alter table public.readings enable row level security;
alter table public.alerts enable row level security;
alter table public.work_orders enable row level security;
alter table public.user_profiles enable row level security;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.user_profiles
    where supabase_user_id = auth.uid() and role = 'Admin'
  );
$$;

drop policy if exists "authenticated users can read maintenance data"
  on public.equipment;
drop policy if exists "authenticated users can read parameters"
  on public.parameters;
drop policy if exists "authenticated users can read readings"
  on public.readings;
drop policy if exists "authenticated users can submit readings"
  on public.readings;
drop policy if exists "authenticated users can read alerts"
  on public.alerts;
drop policy if exists "authenticated users can read work orders"
  on public.work_orders;
drop policy if exists "admins manage profiles"
  on public.user_profiles;
drop policy if exists "users can read own profile"
  on public.user_profiles;
drop policy if exists "admins can manage profiles"
  on public.user_profiles;

create policy "authenticated users can read maintenance data"
on public.equipment for select to authenticated using (true);

create policy "authenticated users can read parameters"
on public.parameters for select to authenticated using (true);

create policy "authenticated users can read readings"
on public.readings for select to authenticated using (true);

create policy "authenticated users can submit readings"
on public.readings for insert to authenticated with check (true);

create policy "authenticated users can read alerts"
on public.alerts for select to authenticated using (true);

create policy "authenticated users can read work orders"
on public.work_orders for select to authenticated using (true);

create policy "users can read own profile"
on public.user_profiles for select to authenticated
using (public.is_admin() or supabase_user_id = auth.uid());

create policy "admins can manage profiles"
on public.user_profiles for all to authenticated
using (public.is_admin())
with check (public.is_admin());

insert into public.user_profiles (supabase_user_id, email, display_name, role)
select id, email, coalesce(raw_user_meta_data->>'name', email), 'Admin'
from auth.users
where lower(email) = lower('bsankara1609@gmail.com')
on conflict (supabase_user_id) do update
set email = excluded.email,
    display_name = excluded.display_name,
    role = 'Admin',
    updated_at = now();
