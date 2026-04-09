from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Render / production: set DATABASE_URL to your Postgres URL (Internal URL on Render is fine for the API).
    # Local dev: SQLite default works when you run from the `backend/` directory.
    database_url: str = "sqlite:///./littlebuggy.db"

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
