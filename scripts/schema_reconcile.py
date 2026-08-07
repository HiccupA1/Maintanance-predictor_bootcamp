"""
Schema reconciliation toolkit: live Supabase PostgreSQL ↔ SQLAlchemy metadata.

This script is intentionally repo-local and lightweight:
- Reads DATABASE_URL from environment (or project .env via app settings).
- Introspects the live database schema (public).
- Introspects SQLAlchemy ORM schema via Base.metadata.
- Produces a JSON snapshot of both and a human-readable diff.

Run examples (from Maintanance-predictor_bootcamp/):
  set -a && source .env && python scripts/schema_reconcile.py snapshot --out kavia-docs/schema/live_schema.json
  set -a && source .env && python scripts/schema_reconcile.py diff --out kavia-docs/schema/schema_diff.md

Notes:
- The live DB is the source of truth for this reconciliation task.
- The script does not mutate the DB.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.engine import Engine

# Import models for side-effect registration on Base.metadata.
import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base


@dataclass(frozen=True)
class ColumnSpec:
    """A normalized column description used for diffing."""

    name: str
    type: str
    nullable: bool | None
    default: str | None


def _normalize_type(type_str: str) -> str:
    """Normalize backend-specific type spellings into stable strings."""
    t = type_str.upper()
    # Keep UUID/JSONB/TIMESTAMPTZ distinct; normalize common aliases.
    t = t.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ")
    t = t.replace("DOUBLE PRECISION", "FLOAT8")
    t = t.replace("CHARACTER VARYING", "VARCHAR")
    return t


def _normalize_default(default: Any) -> str | None:
    """Normalize defaults to stable string values."""
    if default is None:
        return None
    return str(default)


def _engine_from_env() -> Engine:
    """Build SQLAlchemy engine using app settings (which read project .env)."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set (settings.database_url empty).")
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def _live_schema(engine: Engine, schema: str = "public") -> dict[str, Any]:
    """Return a JSON-serializable description of the live DB schema."""
    ins = inspect(engine)
    tables: dict[str, Any] = {}
    for table in sorted(ins.get_table_names(schema=schema)):
        cols = []
        for c in ins.get_columns(table, schema=schema):
            cols.append(
                ColumnSpec(
                    name=c["name"],
                    type=_normalize_type(str(c["type"])),
                    nullable=c.get("nullable"),
                    default=_normalize_default(c.get("default")),
                ).__dict__
            )
        tables[table] = {
            "columns": cols,
            "pk": ins.get_pk_constraint(table, schema=schema),
            "fks": ins.get_foreign_keys(table, schema=schema),
            "uqs": ins.get_unique_constraints(table, schema=schema),
            "indexes": ins.get_indexes(table, schema=schema),
        }
    return {"schema": schema, "tables": tables}


def _orm_schema(metadata: MetaData) -> dict[str, Any]:
    """Return a JSON-serializable description of ORM (SQLAlchemy) schema."""
    tables: dict[str, Any] = {}
    for name, table in sorted(metadata.tables.items(), key=lambda kv: kv[0]):
        cols = []
        for col in table.columns:
            cols.append(
                ColumnSpec(
                    name=col.name,
                    type=_normalize_type(str(col.type)),
                    nullable=col.nullable,
                    default=_normalize_default(col.server_default.arg if col.server_default is not None else None),
                ).__dict__
            )
        tables[name] = {
            "columns": cols,
            "pk": [c.name for c in table.primary_key.columns] if table.primary_key else [],
            "fks": [
                {
                    "constrained_columns": [fk.parent.name],
                    "referred_table": fk.column.table.name,
                    "referred_columns": [fk.column.name],
                    "ondelete": fk.ondelete,
                }
                for fk in table.foreign_keys
            ],
            "indexes": [
                {"name": idx.name, "columns": [c.name for c in idx.columns], "unique": idx.unique}
                for idx in table.indexes
            ],
            "unique_constraints": [
                {"name": uc.name, "columns": [c.name for c in uc.columns]}
                for uc in table.constraints
                if uc.__class__.__name__ == "UniqueConstraint"
            ],
        }
    return {"tables": tables}


def _index_by_name(cols: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {c["name"]: c for c in cols}


def _diff(live: dict[str, Any], orm: dict[str, Any]) -> str:
    """Return a human-readable Markdown diff summary."""
    live_tables = set(live["tables"].keys())
    orm_tables = set(orm["tables"].keys())

    lines: list[str] = []
    lines.append("# Schema Diff (Live Supabase DB → ORM)")
    lines.append("")
    lines.append("This diff treats the *live database* as the source of truth.")
    lines.append("")

    missing_in_orm = sorted(live_tables - orm_tables)
    extra_in_orm = sorted(orm_tables - live_tables)

    if missing_in_orm:
        lines.append("## Tables missing in ORM")
        for t in missing_in_orm:
            lines.append(f"- `{t}`")
        lines.append("")
    if extra_in_orm:
        lines.append("## Tables present in ORM but missing in live DB")
        for t in extra_in_orm:
            lines.append(f"- `{t}`")
        lines.append("")

    common = sorted(live_tables & orm_tables)
    for t in common:
        lcols = _index_by_name(live["tables"][t]["columns"])
        ocols = _index_by_name(orm["tables"][t]["columns"])
        missing_cols = sorted(set(lcols) - set(ocols))
        extra_cols = sorted(set(ocols) - set(lcols))
        changed: list[str] = []

        for cn in sorted(set(lcols) & set(ocols)):
            lc, oc = lcols[cn], ocols[cn]
            if lc["type"] != oc["type"]:
                changed.append(f"- `{cn}` type ORM `{oc['type']}` != LIVE `{lc['type']}`")
            if bool(lc["nullable"]) != bool(oc["nullable"]):
                changed.append(
                    f"- `{cn}` nullable ORM `{oc['nullable']}` != LIVE `{lc['nullable']}`"
                )
            # Defaults can differ in formatting; still report if clearly different.
            if (lc["default"] or None) != (oc["default"] or None):
                changed.append(
                    f"- `{cn}` default ORM `{oc['default']}` != LIVE `{lc['default']}`"
                )

        if missing_cols or extra_cols or changed:
            lines.append(f"## Table `{t}`")
            if missing_cols:
                lines.append("### Columns missing in ORM")
                for cn in missing_cols:
                    lines.append(f"- `{cn}` (LIVE `{lcols[cn]['type']}`)")
            if extra_cols:
                lines.append("### Columns extra in ORM")
                for cn in extra_cols:
                    lines.append(f"- `{cn}` (ORM `{ocols[cn]['type']}`)")
            if changed:
                lines.append("### Column mismatches")
                lines.extend(changed)
            lines.append("")

    if len(lines) <= 4:
        lines.append("No differences detected.")

    return "\n".join(lines) + "\n"


# PUBLIC_INTERFACE
def main() -> None:
    """CLI entrypoint for schema snapshot/diff generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    snap = sub.add_parser("snapshot", help="Write live schema JSON snapshot.")
    snap.add_argument("--out", required=True, help="Output JSON path.")

    diff = sub.add_parser("diff", help="Write Markdown diff (live vs ORM).")
    diff.add_argument("--out", required=True, help="Output Markdown path.")
    diff.add_argument("--schema", default="public", help="DB schema name (default public).")

    args = parser.parse_args()

    engine = _engine_from_env()
    live = _live_schema(engine, schema=getattr(args, "schema", "public"))
    orm = _orm_schema(Base.metadata)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.cmd == "snapshot":
        out_path.write_text(json.dumps(live, indent=2) + "\n", encoding="utf-8")
        return

    if args.cmd == "diff":
        out_path.write_text(_diff(live, orm), encoding="utf-8")
        return


if __name__ == "__main__":
    main()
