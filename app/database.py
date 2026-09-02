# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Database engine, session, and dependency for ovos-opendata-server."""

from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create (and cache) the SQLAlchemy engine from current settings.

    Lazily created on first use so importing this module never requires
    DATABASE_URL to be set.
    """
    database_url = get_settings().database_url
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


@lru_cache
def get_session_factory() -> sessionmaker:
    """Return (and cache) the session factory bound to the lazy engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
