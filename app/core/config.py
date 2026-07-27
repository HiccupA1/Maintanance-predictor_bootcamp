"""Application configuration.

Environment-driven settings for the Work Order Management backend. No secrets
are hard-coded; values are sourced from the environment (and an optional .env
file) so the app can be configured per-environment without code changes.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# PUBLIC_INTERFACE
class Settings(BaseSettings):
    """Runtime settings loaded from environment variables.

    Attributes:
        app_name: Human-readable application title used in OpenAPI metadata.
        app_version: Semantic version string surfaced in OpenAPI metadata.
        database_url: SQLAlchemy database URL. Defaults to a local PostgreSQL
            instance; tests override this with a SQLite URL.
        problem_base_uri: Base URI used to build RFC7807 ``type`` values per
            error ``code``.
    """

    app_name: str = "Work Order Management API"
    app_version: str = "0.2.0"
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/workorders"
    )
    problem_base_uri: str = "https://api.workorders.local/errors"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Returns:
        Settings: The process-wide settings singleton.
    """
    return Settings()
