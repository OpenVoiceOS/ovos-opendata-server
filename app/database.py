# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Database engine, session, and dependency for ovos-opendata-server."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _get_database_url() -> str:
    """Return DATABASE_URL from environment or raise RuntimeError."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "See .env.example for configuration."
        )
    return url


DATABASE_URL: str = _get_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
