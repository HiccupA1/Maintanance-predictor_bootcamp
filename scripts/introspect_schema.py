"""Dump the ``public`` schema's structure from a Postgres database, read-only.

Used to compare a deployed database (e.g. the live Supabase project) against
the Alembic baseline. It reads only the system catalog: columns, indexes,
constraints, RLS flags, policies, functions, extensions and migration-tracking
tables. It never reads table rows and runs inside a READ ONLY transaction.

Usage (the connection string is taken from the environment and never printed):

    $env:INTROSPECT_DATABASE_URL = "postgresql://..."   # PowerShell
    python scripts/introspect_schema.py reports/live_schema.txt
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

QUERIES = {
    "server_version": "show server_version",
    "extensions": "select extname, extversion from pg_extension order by 1",
    "tracking_tables": """
        select to_regclass('public.alembic_version')::text,
               to_regclass('supabase_migrations.schema_migrations')::text""",
    "columns": """
        select table_name, column_name, data_type, is_nullable, column_default
        from information_schema.columns
        where table_schema = 'public'
        order by table_name, ordinal_position""",
    "indexes": """
        select tablename, indexname, indexdef from pg_indexes
        where schemaname = 'public' order by tablename, indexname""",
    "constraints": """
        select conrelid::regclass::text, conname, contype,
               pg_get_constraintdef(oid)
        from pg_constraint
        where connamespace = 'public'::regnamespace
          -- Postgres 18+ also catalogs NOT NULL as constraints; nullability
          -- is already covered by the columns section.
          and contype <> 'n'
        order by 1, 2""",
    "rls": """
        select relname, relrowsecurity from pg_class
        where relnamespace = 'public'::regnamespace and relkind in ('r', 'p')
        order by 1""",
    "policies": """
        select tablename, policyname, cmd, roles::text, qual, with_check
        from pg_policies where schemaname = 'public' order by 1, 2""",
    "functions": """
        select proname from pg_proc
        where pronamespace = 'public'::regnamespace order by 1""",
}


def main() -> int:
    url = os.environ.get("INTROSPECT_DATABASE_URL")
    if not url:
        print("Set INTROSPECT_DATABASE_URL first.", file=sys.stderr)
        return 2
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/schema.txt")
    out.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url)
    lines: list[str] = []
    with engine.connect() as conn:
        conn.execute(text("set transaction read only"))
        for name, sql in QUERIES.items():
            lines.append(f"## {name}")
            for row in conn.execute(text(sql)):
                lines.append(
                    " | ".join("" if v is None else str(v) for v in row)
                )
            lines.append("")
        conn.rollback()

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
