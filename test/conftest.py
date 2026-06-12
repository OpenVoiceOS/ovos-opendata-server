# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Shared pytest fixtures for ovos-opendata-server tests."""

import os

# Must be set before any app module is imported
os.environ["DATABASE_URL"] = "sqlite:///./test_ovos.db"
os.environ["MAX_AUDIO_SIZE_MB"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Intent, Utterance, WakeWord  # noqa: E402

_SQLITE_URL = "sqlite:///./test_ovos.db"
_engine = create_engine(_SQLITE_URL, connect_args={"check_same_thread": False})
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Create all tables once at module import
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    """Yield a test database session backed by the test SQLite DB."""
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


def pytest_configure(config):
    """Ensure test DB is clean at session start."""
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables before each test for isolation."""
    yield
    db = _TestingSessionLocal()
    try:
        db.query(Intent).delete()
        db.query(WakeWord).delete()
        db.query(Utterance).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient with the SQLite test DB override active."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def db():
    """Yield a database session for direct DB manipulation in tests."""
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
