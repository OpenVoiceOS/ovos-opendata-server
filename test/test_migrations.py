# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests that the hand-written Alembic migrations build (and tear down) the
same schema as the SQLAlchemy models."""

import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings
from app.database import Base

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def migrated_db_url(monkeypatch, tmp_path):
    """Point DATABASE_URL at a fresh tmp SQLite file for the duration of the test."""
    db_path = tmp_path / "migrations_test.db"
    db_url = f"sqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    yield db_url

    get_settings.cache_clear()


def _alembic_config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    return cfg


def test_upgrade_head_creates_all_model_tables(migrated_db_url):
    cfg = _alembic_config()

    command.upgrade(cfg, "head")

    engine = create_engine(migrated_db_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    engine.dispose()

    expected_tables = set(Base.metadata.tables.keys())
    assert expected_tables <= tables
    assert "alembic_version" in tables


def test_downgrade_base_removes_all_model_tables(migrated_db_url):
    cfg = _alembic_config()

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(migrated_db_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    engine.dispose()

    model_tables = set(Base.metadata.tables.keys())
    assert not (model_tables & tables)
