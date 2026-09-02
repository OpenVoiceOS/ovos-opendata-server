# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for the pydantic-settings based configuration module."""

import os
import subprocess
import sys

from app.config import Settings, get_settings


def test_app_importable_without_database_url():
    """`import app.main` must succeed even with DATABASE_URL unset."""
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_settings_picks_up_max_audio_size_mb_from_env(monkeypatch):
    """Settings should read MAX_AUDIO_SIZE_MB from the environment."""
    monkeypatch.setenv("MAX_AUDIO_SIZE_MB", "42")
    get_settings.cache_clear()
    try:
        settings = Settings()
        assert settings.max_audio_size_mb == 42
    finally:
        get_settings.cache_clear()
