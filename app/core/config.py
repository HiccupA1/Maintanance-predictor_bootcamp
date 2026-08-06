"""Application configuration.

Environment-driven settings for the Work Order Management backend. No secrets
are hard-coded; values are sourced from the environment (and an optional .env
file) so the app can be configured per-environment without code changes.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
        supabase_url: Supabase project URL (e.g. https://<project-ref>.supabase.co).
        supabase_publishable_key: Supabase publishable API key (sb_publishable_...).
            This is safe to use in browsers, but we keep it on the backend to
            support discovery/verification endpoints when needed.
        supabase_secret_key: Supabase secret API key (sb_secret_...).
            This MUST NOT be exposed to browsers. The backend uses it only for
            server-to-server operations (if needed) and should generally prefer
            database connections for data access.
        supabase_jwks_url: Optional explicit JWKS endpoint. If empty, defaults
            to `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`.
        supabase_jwt_audience: Optional JWT `aud` to validate (often "authenticated").
            If empty, audience validation is skipped.
        enable_dev_identity_shim: When true, allows the legacy dev-only identity
            shim via X-User-Role / X-User-Name headers. MUST be disabled in
            production.
    """

    app_name: str = "Work Order Management API"
    app_version: str = "0.2.0"
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/workorders"
    )
    problem_base_uri: str = "https://api.workorders.local/errors"
    cors_origins: str = ""
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwks_url: str = ""
    supabase_jwt_audience: str = ""
    enable_dev_identity_shim: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        """Return configured comma-separated browser origins."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        # Keep API and seed commands on the same project-local configuration.
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Returns:
        Settings: The process-wide settings singleton.
    """
    return Settings()
