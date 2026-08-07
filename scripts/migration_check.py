"""
Migration drift checker.

Goals:
- Detect whether alembic_version in the live DB matches the repository head.
- Detect whether ORM metadata tables exist in the live DB and vice-versa.

Run (from Maintanance-predictor_bootcamp/):
  set -a && source .env && python scripts/migration_check.py

This is read-only (no DB mutations).
"""

from __future__ import annotations

from dataclasses import dataclass

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

# Import models so metadata is complete.
import app.models  # noqa: F401
from app.core.config import PROJECT_ROOT, get_settings
from app.db.base import Base


@dataclass(frozen=True)
class CheckResult:
    """A single drift check result."""

    ok: bool
    message: str


def _alembic_script() -> ScriptDirectory:
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", "alembic")
    return ScriptDirectory.from_config(cfg)


def _repo_head_revision() -> str:
    script = _alembic_script()
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("No Alembic head revision found.")
    return head


def _db_current_revision(engine) -> str | None:
    with engine.connect() as c:
        try:
            return c.execute(text("select version_num from alembic_version")).scalar()
        except Exception:
            return None


def _table_sets(engine, schema="public") -> set[str]:
    ins = inspect(engine)
    return set(ins.get_table_names(schema=schema))


def _run_checks() -> list[CheckResult]:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

    results: list[CheckResult] = []

    repo_head = _repo_head_revision()
    db_rev = _db_current_revision(engine)

    if db_rev is None:
        results.append(
            CheckResult(
                ok=False,
                message="Live DB has no alembic_version table (migrations not tracked via Alembic?).",
            )
        )
    elif db_rev != repo_head:
        results.append(
            CheckResult(
                ok=False,
                message=f"Alembic drift: live DB revision={db_rev!r} repo head={repo_head!r}.",
            )
        )
    else:
        results.append(
            CheckResult(ok=True, message=f"Alembic revision matches head: {repo_head}.")
        )

    live_tables = _table_sets(engine)
    orm_tables = set(Base.metadata.tables.keys())

    missing_in_live = sorted(orm_tables - live_tables)
    extra_in_live = sorted(live_tables - orm_tables)

    if missing_in_live:
        results.append(
            CheckResult(
                ok=False,
                message=f"Tables missing in live DB (present in ORM): {', '.join(missing_in_live)}",
            )
        )
    else:
        results.append(CheckResult(ok=True, message="All ORM tables exist in live DB."))

    # In Supabase there can be many non-ORM tables in other schemas; we restrict to public.
    # Still, extra tables in public can signal drift.
    if extra_in_live:
        results.append(
            CheckResult(
                ok=True,
                message=f"Note: extra tables in live public schema (not in ORM): {', '.join(extra_in_live)}",
            )
        )

    return results


# PUBLIC_INTERFACE
def main() -> None:
    """CLI entrypoint to print drift checks."""
    results = _run_checks()
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"[{status}] {r.message}")
    # Non-zero exit code on failures for CI usage.
    if any(not r.ok for r in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
