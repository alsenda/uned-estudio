"""Database engine and session management (vendored from quiz-app's app/db.py)."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app import models

    models.Base.metadata.create_all(bind=get_engine())
