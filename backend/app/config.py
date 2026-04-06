from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Render / production: set DATABASE_URL to your Postgres URL (Internal URL on Render is fine for the API).
    # Local dev: SQLite default works when you run from the `backend/` directory.
    database_url: str = "sqlite:///./littlebuggy.db"

    # Comma-separated browser origins allowed to call the API (no spaces), or "*" for any origin.
    # Production: set to your static site origin(s), e.g. https://littlebuggy.onrender.com
    # With "*", credentials are disabled (fine for this read-only public API).
    cors_origins: str = "*"

    # Admin-only: POST /api/admin/homepage-snapshot/regenerate (X-Admin-Token header). Leave unset to disable.
    admin_homepage_token: str | None = None

    # If set, regenerate endpoint also writes this path (API must have write permission — usually local dev only).
    # Example from repo root via backend cwd: ../public/data/homepage-summary.json
    homepage_summary_output_path: str | None = None


settings = Settings()
