"""Alembic migration environment.

Uses the application's configured database URL and ORM metadata so migrations
stay in sync with the models without duplicating configuration.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Import models so their tables register on Base.metadata.
import app.models  # noqa: F401  (side-effect import)
from alembic import context
from app.core.config import get_settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Schemas owned by Supabase, not by this application's migrations.
EXTERNAL_SCHEMAS = {"auth", "storage", "extensions"}


def include_object(obj, name, type_, reflected, compare_to):
    """Exclude references into Supabase-managed schemas from autogenerate.

    The baseline adds ``user_profiles.supabase_user_id -> auth.users(id)``
    only on Supabase. The ORM cannot model ``auth.users``, so without this
    filter ``alembic check`` would report that foreign key as drift.
    """
    if type_ == "foreign_key_constraint" and reflected:
        if getattr(obj.referred_table, "schema", None) in EXTERNAL_SCHEMAS:
            return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
