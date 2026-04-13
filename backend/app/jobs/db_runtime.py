"""
Guards for cron / one-off jobs that must share the API's Postgres on Render.
"""

from __future__ import annotations

import sys

from app.settings import database_kind_from_url, is_render_runtime, settings


def exit_if_render_database_not_postgres(job_name: str) -> None:
    """
    On Render, snapshot jobs must use the linked Postgres URL. If ``DATABASE_URL`` is missing or
    still the SQLite default, inserts go to an ephemeral local file — ``GET /api/homepage-summary``
    on the web service (which uses Postgres) will never see those rows.
    """
    if not is_render_runtime():
        return
    if database_kind_from_url(settings.database_url) == "postgresql":
        return
    kind = database_kind_from_url(settings.database_url)
    print(
        f"{job_name}: On Render, DATABASE_URL must be PostgreSQL (same DB as littlebuggy-api). "
        f"Current URL resolves to backend={kind!r} — refusing to write snapshots to the wrong store.",
        file=sys.stderr,
    )
    sys.exit(1)
