# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Application settings, loaded from environment variables (and .env)."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for ovos-opendata-server.

    All fields are read from environment variables (uppercased field name)
    and optionally from a `.env` file in the working directory.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ovos_opendata.db"
    max_audio_size_mb: int = 10
    api_key: Optional[str] = None
    rate_limit: str = "60/minute"
    dashboard_cache_ttl: int = 60


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
