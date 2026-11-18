# Database Migrations

Alembic is the only tool that changes the database schema (ADR-0009). The
migrations live in `alembic/versions/`, starting from `0001_baseline`.
Do not run `supabase db push`, and do not edit tables in the Supabase dashboard.

## Day to day

1. **Write the migration.** Change the ORM models, then run
   `alembic revision --autogenerate -m "short description"`. Review the
   generated file by hand. Autogenerate misses some things, including check
   constraints, RLS policies, functions and data backfills, so add those
   explicitly with `op.execute`.
2. **Every migration needs a working `downgrade()`.** If a change cannot be
   reversed, say why in the docstring.
3. **Use expand/contract for breaking changes.** Add the new column or table
   and deploy code that writes to both. Backfill. Switch reads. Drop the old
   structure in a later release. Never rename or drop something the running
   release still reads.
4. **Never edit a migration that has been applied anywhere.** Write a new one.
5. **Let CI check it.** The `migrations` job (blocking) will:
   - build an empty Postgres to head;
   - run `alembic check`, which fails if the models and migrations disagree;
   - round-trip downgrade and upgrade;
   - repeat the build with a Supabase `auth` stub;
   - publish the resulting schema dump as the `baseline-schema` artifact.
6. **Release.** Apply to staging first, then production, from the release
   pipeline or a reviewed manual step:
   ```bash
   alembic upgrade head        # DATABASE_URL points at the target
   alembic current             # confirm the expected head
   ```
   Take or confirm a backup before every production apply.

## One-time adoption on the live database (`alembic stamp`)

The live Supabase database already contains the baseline schema, because it
was built from the now-archived `supabase/migrations`. Alembic is told this
with `alembic stamp`. That command creates the `alembic_version` table and
writes one row to it. It does not change any other table.

**This needs the project owner's explicit approval, and the schema diff in
step 2 must be clean.**

1. **Dump live** (read-only: catalog queries in a READ ONLY transaction):
   ```powershell
   $env:INTROSPECT_DATABASE_URL = "postgresql://..."   # live; do not paste into chats or tickets
   python scripts/introspect_schema.py reports/live_schema.txt
   Remove-Item Env:INTROSPECT_DATABASE_URL
   ```
2. **Compare it with the baseline.** Use the `baseline-schema` CI artifact,
   or build one on any empty Postgres that has the auth stub:
   ```bash
   git diff --no-index reports/baseline_schema.txt reports/live_schema.txt
   ```
   These differences are expected and fine:
   - `server_version`;
   - `extensions` (Supabase installs extra ones);
   - `tracking_tables`, plus `alembic_version` rows in the baseline dump.

   **Any other difference stops the procedure.** Until the first stamp, the
   baseline has not been applied anywhere, so correct it to match live (in a
   reviewed PR). Then re-run CI and repeat this comparison.
3. **Back up.** Confirm a recent Supabase backup exists (Dashboard → Database
   → Backups). Otherwise take a schema and data dump.
4. **Stamp:**
   ```bash
   DATABASE_URL="postgresql+psycopg2://..." alembic stamp 0001_baseline
   DATABASE_URL="postgresql+psycopg2://..." alembic current   # 0001_baseline (head)
   DATABASE_URL="postgresql+psycopg2://..." alembic check     # no drift
   ```
5. **Roll back if needed:** `drop table public.alembic_version;` This returns
   the database exactly to its pre-stamp state.
6. **Record it:** add the date, who stamped, and the diff result to the
   release notes.

After adoption, every schema change, including the D17 RLS fix, goes out
through `alembic upgrade head` as described above.

## Bootstrap the first Admin

There is no admin email in any migration. For each environment:

1. In the Supabase Dashboard, go to Authentication → Users and create or
   invite the administrator. Their password is set there.
2. Run:
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg2://..."
   $env:BOOTSTRAP_ADMIN_EMAIL = "admin@client.example"
   python scripts/seed_admin.py
   ```
3. That Admin then assigns every other role in the app under Admin → Users.
