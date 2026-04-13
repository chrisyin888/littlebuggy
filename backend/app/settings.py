import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Required for production (Render): Postgres URL from the dashboard / Blueprint (see root render.yaml).
    # Local dev: SQLite default is fine when cwd is `backend/`.
    database_url: str = "sqlite:///./littlebuggy.db"

    @field_validator("database_url")
    @classmethod
    def _database_url_non_empty(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError(
                "DATABASE_URL is empty. Set it to your Postgres connection string on Render, "
                "or use sqlite:///./littlebuggy.db for local dev."
            )
        return s

    # Comma-separated browser origins (no spaces), or "*" for any origin.
    # Render: set via CORS_ORIGINS (see root render.yaml — includes https://littlebuggy.ca and www).
    # Local: "*" is fine; or list http://localhost:5173 if you lock CORS while testing.
    cors_origins: str = "*"

    # Admin-only: POST /api/admin/homepage-snapshot/regenerate (X-Admin-Token header). Leave unset to disable.
    admin_homepage_token: str | None = None

    # If set, regenerate endpoint also writes this path (API must have write permission — usually local dev only).
    # Example from repo root via backend cwd: ../public/data/homepage-summary.json
    homepage_summary_output_path: str | None = None


settings = Settings()


def is_render_runtime() -> bool:
    """Render sets RENDER=true on web services and cron jobs."""
    return os.environ.get("RENDER", "").strip().lower() in ("true", "1", "yes")


def database_kind_from_url(url: str) -> str:
    """Coarse driver label for logs and /health (never log secrets)."""
    raw = (url or "").strip()
    if not raw:
        return "other"
    try:
        dialect = make_url(raw).drivername.lower().split("+", 1)[0]
    except Exception:
        # Unparseable strings: best-effort scheme match (same rules as SQLAlchemy URLs).
        lowered = raw.lower()
        if ":" not in lowered:
            return "other"
        scheme = lowered.split(":", 1)[0]
        dialect = scheme.split("+", 1)[0]
    if dialect == "sqlite":
        return "sqlite"
    if dialect in ("postgres", "postgresql"):
        return "postgresql"
    return "other"


def postgres_required_message_if_misconfigured() -> str | None:
    """
    On Render, SQLite is ephemeral and not shared across instances — homepage snapshot API must use Postgres.

    Returns operator-facing detail text if misconfigured, else None.
    """
    if not is_render_runtime():
        return None
    if database_kind_from_url(settings.database_url) == "postgresql":
        return None
    return (
        "On Render, DATABASE_URL must be a PostgreSQL connection string (postgres:// or postgresql://, "
        "including SQLAlchemy forms such as postgresql+psycopg://). SQLite is ephemeral on web services and "
        "is only supported for local development. In the Render dashboard: open this service → Environment → "
        "set DATABASE_URL from your Postgres instance (Internal Database URL), then redeploy."
    )
