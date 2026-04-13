import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.routes import virus_trends, wait_times
from app.settings import (
    database_kind_from_url,
    postgres_required_message_if_misconfigured,
    settings,
)
from app.database import Base, engine
from app.models import Visit, VirusTrendsLatest  # noqa: F401 — register tables for create_all
from app.services.db_schema import ensure_trend_snapshot_columns

log = logging.getLogger("littlebuggy.api")


def _parse_cors_origins(raw: str) -> list[str]:
    s = raw.strip()
    if not s or s == "*":
        return ["*"]
    return [o.strip() for o in s.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # V1: create tables if missing (add Alembic migrations when the schema stabilizes).
    kind = database_kind_from_url(settings.database_url)
    log.info(
        "LittleBuggy API startup: DATABASE_URL backend=%s — homepage snapshot reads/writes table trend_snapshots.",
        kind,
    )
    mis = postgres_required_message_if_misconfigured()
    if mis:
        log.error(
            "Homepage snapshot API will return HTTP 503 for regenerate and homepage-summary until fixed: %s",
            mis,
        )
    Base.metadata.create_all(bind=engine)
    ensure_trend_snapshot_columns(engine)
    yield


app = FastAPI(title="LittleBuggy API", version="0.1.0", lifespan=lifespan)

_origins = _parse_cors_origins(settings.cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(virus_trends.public_router)
app.include_router(wait_times.router)


@app.get("/health")
def health():
    kind = database_kind_from_url(settings.database_url)
    mis = postgres_required_message_if_misconfigured()
    return {
        "status": "ok",
        "database": {
            "backend": kind,
            "homepage_snapshot_api_configured": mis is None,
            **({"configuration_error": mis} if mis else {}),
        },
        "routes": {
            "wait_times": "/wait-times",
            "virus_trends": "/virus-trends",
            "api_status": "/api/status",
            "homepage_summary": "/api/homepage-summary",
        },
    }
