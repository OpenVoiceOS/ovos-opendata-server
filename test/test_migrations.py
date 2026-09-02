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


def test_upgrade_head_adds_session_default_column(migrated_db_url):
    """0003 adds the nullable intents.session_default column on top of 0001+0002."""
    cfg = _alembic_config()

    command.upgrade(cfg, "head")

    engine = create_engine(migrated_db_url)
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("intents")}
    engine.dispose()

    assert "session_default" in columns


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


def test_upgrade_head_stamps_preexisting_baseline(migrated_db_url):
    """Pre-alembic DBs (Base.metadata.create_all, no alembic_version) upgrade cleanly.

    Simulates a production database that existed before alembic was introduced:
    the 0001 tables are already there (created via Base.metadata.create_all) but
    there is no alembic_version table. 'alembic upgrade head' must stamp 0001
    instead of crashing on 'table already exists', then proceed to head.
    """
    from sqlalchemy import create_engine, inspect as sa_inspect
    import sqlalchemy as sa

    # Build a throwaway metadata snapshot matching the 0001 baseline schema
    # (intents/wake_words/stt without the columns 0002/0003 add), mirroring how
    # a production database predating alembic was originally created via
    # Base.metadata.create_all. No alembic_version table is created.
    engine = create_engine(migrated_db_url)

    baseline_metadata = sa.MetaData()
    sa.Table(
        "intents",
        baseline_metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("utterance", sa.String(), nullable=False),
        sa.Column("intent", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("match_data", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    sa.Table(
        "wake_words",
        baseline_metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("plugin", sa.String(), nullable=True),
        sa.Column("plugin_config", sa.String(), nullable=True),
        sa.Column("audio", sa.LargeBinary(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    sa.Table(
        "stt",
        baseline_metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("plugin", sa.String(), nullable=True),
        sa.Column("plugin_config", sa.String(), nullable=True),
        sa.Column("audio", sa.LargeBinary(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    baseline_metadata.create_all(engine)
    engine.dispose()

    cfg = _alembic_config()
    # This is the entrypoint's migration path: 'alembic upgrade head'. It must
    # not crash with "table intents already exists".
    command.upgrade(cfg, "head")

    engine = create_engine(migrated_db_url)
    inspector = sa_inspect(engine)
    tables = set(inspector.get_table_names())
    intent_columns = {c["name"] for c in inspector.get_columns("intents")}
    engine.dispose()

    assert "alembic_version" in tables
    assert {"pipeline", "core_version", "session_default"} <= intent_columns
