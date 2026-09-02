# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Paginated read endpoints for querying collected OVOS metrics."""

import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Intent, Utterance, WakeWord
from app.schemas import IntentRecord, PaginatedResponse, UtteranceRecord, WakeWordRecord

router = APIRouter()

_MAX_LIMIT = 500


def _paginate(query, page: int, limit: int) -> tuple:
    """Return (items, total) for a SQLAlchemy query with pagination applied.

    Args:
        query: SQLAlchemy select query.
        page: 1-based page number.
        limit: Number of records per page.

    Returns:
        Tuple of (list of ORM objects, total count).
    """
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total


@router.get("/intents", response_model=PaginatedResponse[IntentRecord])
def list_intents(
    lang: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=_MAX_LIMIT),
    db: Session = Depends(get_db),
) -> PaginatedResponse[IntentRecord]:
    """Return a paginated list of intent records with optional filters.

    Args:
        lang: Filter by language tag (case-insensitive).
        intent: Filter by intent name (exact match).
        date_from: Include records at or after this timestamp.
        date_to: Include records at or before this timestamp.
        page: Page number (1-based).
        limit: Records per page (max 500).
        db: Database session.

    Returns:
        PaginatedResponse containing IntentRecord items.
    """
    q = db.query(Intent)
    if lang:
        q = q.filter(Intent.language == lang.lower())
    if intent:
        q = q.filter(Intent.intent == intent)
    if date_from:
        q = q.filter(Intent.timestamp >= date_from)
    if date_to:
        q = q.filter(Intent.timestamp <= date_to)
    q = q.order_by(Intent.timestamp.desc())
    items, total = _paginate(q, page, limit)
    records = [
        IntentRecord(
            id=r.id,
            intent=r.intent,
            language=r.language,
            utterance=r.utterance,
            pipeline=r.pipeline,
            core_version=r.core_version,
            session_default=r.session_default,
            created_at=r.timestamp,
        )
        for r in items
    ]
    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


@router.get("/wake_words", response_model=PaginatedResponse[WakeWordRecord])
def list_wake_words(
    name: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    plugin: Optional[str] = Query(None),
    lang: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=_MAX_LIMIT),
    db: Session = Depends(get_db),
) -> PaginatedResponse[WakeWordRecord]:
    """Return a paginated list of wake-word records (audio excluded).

    Args:
        name: Filter by wake-word name.
        model: Filter by model identifier.
        plugin: Filter by plugin name.
        lang: Filter by language tag (case-insensitive).
        page: Page number (1-based).
        limit: Records per page (max 500).
        db: Database session.

    Returns:
        PaginatedResponse containing WakeWordRecord items.
    """
    q = db.query(WakeWord)
    if name:
        q = q.filter(WakeWord.name == name)
    if model:
        q = q.filter(WakeWord.model == model)
    if plugin:
        q = q.filter(WakeWord.plugin == plugin)
    if lang:
        q = q.filter(WakeWord.language == lang.lower())
    q = q.order_by(WakeWord.timestamp.desc())
    items, total = _paginate(q, page, limit)
    records = [
        WakeWordRecord(
            id=r.id,
            wake_word=r.name,
            model=r.model,
            plugin=r.plugin,
            language=r.language,
            created_at=r.timestamp,
        )
        for r in items
    ]
    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


@router.get("/utterances", response_model=PaginatedResponse[UtteranceRecord])
def list_utterances(
    lang: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    plugin: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=_MAX_LIMIT),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UtteranceRecord]:
    """Return a paginated list of STT utterance records (audio excluded).

    Args:
        lang: Filter by language tag (case-insensitive).
        model: Filter by model name.
        plugin: Filter by plugin name.
        page: Page number (1-based).
        limit: Records per page (max 500).
        db: Database session.

    Returns:
        PaginatedResponse containing UtteranceRecord items.
    """
    q = db.query(Utterance)
    if lang:
        q = q.filter(Utterance.language == lang.lower())
    if model:
        q = q.filter(Utterance.model == model)
    if plugin:
        q = q.filter(Utterance.plugin == plugin)
    q = q.order_by(Utterance.timestamp.desc())
    items, total = _paginate(q, page, limit)
    records = [
        UtteranceRecord(
            id=r.id,
            model=r.model,
            plugin=r.plugin,
            language=r.language,
            created_at=r.timestamp,
        )
        for r in items
    ]
    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )
