# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""SQLAlchemy ORM models for ovos-opendata-server."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base


class Intent(Base):
    """Stores OVOS intent match events submitted by devices."""

    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utterance: Mapped[str] = mapped_column(String, nullable=False)
    intent: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    match_data: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pipeline: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    core_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @validates("language")
    def normalize_language(self, key: str, value: str) -> str:
        """Lowercase and strip the language tag on assignment."""
        if value is None:
            return value
        return value.strip().lower()


class WakeWord(Base):
    """Stores wake-word detection samples with audio data."""

    __tablename__ = "wake_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plugin: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plugin_config: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @validates("language")
    def normalize_language(self, key: str, value: Optional[str]) -> Optional[str]:
        """Lowercase and strip the language tag on assignment."""
        if value is None:
            return value
        return value.strip().lower()


class Utterance(Base):
    """Stores STT utterance samples with audio data."""

    __tablename__ = "stt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transcript: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plugin: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plugin_config: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @validates("language")
    def normalize_language(self, key: str, value: Optional[str]) -> Optional[str]:
        """Lowercase and strip the language tag on assignment."""
        if value is None:
            return value
        return value.strip().lower()
