# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Alembic migration environment for ovos-opendata-server."""

from logging.config import fileConfig

from alembic import context
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config, inspect, pool

from app.config import get_settings
from app.database import Base

# Import models so they register on Base.metadata before target_metadata is read.
import app.models  # noqa: F401

# Alembic Config object, providing access to values within alembic.ini.
config = context.config

# Interpret the config file for Python logging, unless run programmatically
# without a logging section configured.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Resolve the database URL from the application settings."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def stamp_baseline_if_needed(connectable) -> None:
    """Stamp pre-alembic databases at 0001 instead of re-creating existing tables.

    Databases created before alembic was introduced (via Base.metadata.create_all)
    already have the 0001 tables but no alembic_version table. Without this guard,
    'alembic upgrade head' tries to run 0001's create_table again and crashes with
    "table already exists". If the intents table is present but alembic_version is
    not, stamp the revision history at 0001 so upgrade head proceeds from 0002.

    Uses its own short-lived connection (committed and closed before returning)
    so it never leaves an open implicit transaction on the connection alembic's
    own migration run subsequently takes over.
    """
    with connectable.connect() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "intents" in tables and "alembic_version" not in tables:
            script = ScriptDirectory.from_config(config)
            migration_context = MigrationContext.configure(connection)
            migration_context.stamp(script, "0001")
        connection.commit()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    stamp_baseline_if_needed(connectable)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
