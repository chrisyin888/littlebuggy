"""
SQLAlchemy engine and session factory.

All homepage snapshot persistence goes through ``get_db()`` → the same ``DATABASE_URL`` as cron jobs.
``POST /api/admin/.../regenerate`` and ``GET /api/homepage-summary`` must share this database.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from app.config import settings

_url = settings.database_url
_sqlite = _url.strip().lower().startswith("sqlite")

# Sync engine — simple and reliable for V1 cron + API.
_engine_kwargs: dict = {"pool_pre_ping": True}
if _sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(_url, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
