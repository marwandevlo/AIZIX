from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_url = _settings.database_url
_engine_kwargs: dict = {"pool_pre_ping": True}
if _url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Supabase (pgBouncer compatible with pool_pre_ping)
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 15

engine = create_engine(_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
