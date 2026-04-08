from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.routes import virus_trends, wait_times
from app.config import settings
from app.database import Base, engine
from app.services.db_schema import ensure_trend_snapshot_columns


def _parse_cors_origins(raw: str) -> list[str]:
    s = raw.strip()
    if not s or s == "*":
        return ["*"]
    return [o.strip() for o in s.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # V1: create tables if missing (add Alembic migrations when the schema stabilizes).
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
    return {
        "status": "ok",
        "routes": {
            "wait_times": "/wait-times",
            "virus_trends": "/virus-trends",
            "api_status": "/api/status",
            "homepage_summary": "/api/homepage-summary",
        },
    }
