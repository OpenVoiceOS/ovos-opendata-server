# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Pydantic v2 response schemas for ovos-opendata-server."""

from datetime import datetime
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class IntentRecord(BaseModel):
    """Schema for a single intent match record returned by list/query endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    intent: str
    language: str
    utterance: str
    created_at: Optional[datetime] = None


class WakeWordRecord(BaseModel):
    """Schema for a wake-word record (audio excluded from list endpoints)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    wake_word: Optional[str] = None
    model: Optional[str] = None
    plugin: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


class UtteranceRecord(BaseModel):
    """Schema for an STT utterance record (audio excluded from list endpoints)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model: Optional[str] = None
    plugin: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    limit: int
    pages: int


class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard overview."""

    total_intents: int
    total_wake_words: int
    total_utterances: int
    intent_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    wake_word_distribution: Dict[str, int]
