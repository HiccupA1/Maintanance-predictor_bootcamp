-- D17 regression check, run by CI after `alembic upgrade head` on the
-- Supabase stub. It fails (raises) if the Data API roles can reach any
-- application table, or if any application table lacks RLS.
do $$
declare
  t record;
  r text;
begin
  for t in
    select tablename from pg_tables
    where schemaname = 'public' and tablename <> 'alembic_version'
  loop
    if not (select relrowsecurity from pg_class
            where oid = format('public.%I', t.tablename)::regclass) then
      raise exception 'RLS disabled on public.%', t.tablename;
    end if;
    foreach r in array array['anon', 'authenticated'] loop
      if has_table_privilege(r, format('public.%I', t.tablename),
                             'SELECT,INSERT,UPDATE,DELETE') then
        raise exception '% has privileges on public.%', r, t.tablename;
      end if;
    end loop;
  end loop;
  if exists (select 1 from pg_policies where schemaname = 'public') then
    raise exception 'unexpected RLS policies remain on public tables';
  end if;
end
$$;

-- Behavioural check: an authenticated Data API session is denied.
set role authenticated;
do $$
begin
  perform 1 from public.equipment limit 1;
  raise exception 'authenticated could read public.equipment';
exception when insufficient_privilege then
  null;  -- expected
end
$$;
reset role;
