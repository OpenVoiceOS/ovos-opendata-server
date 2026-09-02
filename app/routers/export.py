# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Export endpoints for bulk CSV/JSON download of collected OVOS metrics."""

import csv
import io
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Intent, Utterance, WakeWord

router = APIRouter()

_EXPORT_ROW_CAP = 100_000


@router.get("/intents/export")
def export_intents(
    format: str = Query("csv", pattern="^(csv|json)$"),
    lang: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export intent records as CSV or JSON (max 100k rows).

    Args:
        format: Output format — 'csv' or 'json'.
        lang: Filter by language tag.
        intent: Filter by intent name.
        date_from: Lower bound timestamp filter.
        date_to: Upper bound timestamp filter.
        db: Database session.

    Returns:
        StreamingResponse with appropriate media type.

    Raises:
        HTTPException: 400 for unsupported format.
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
    rows = q.limit(_EXPORT_ROW_CAP).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "intent", "language", "utterance", "timestamp"])
        for r in rows:
            writer.writerow([r.id, r.intent, r.language, r.utterance, r.timestamp])
        output.seek(0)
        return StreamingResponse(
            iter([output.read()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=intents.csv"},
        )
    data = [
        {
            "id": r.id,
            "intent": r.intent,
            "language": r.language,
            "utterance": r.utterance,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return StreamingResponse(
        iter([json.dumps(data)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=intents.json"},
    )


@router.get("/wake_words/export")
def export_wake_words(
    format: str = Query("csv", pattern="^(csv|json)$"),
    name: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    plugin: Optional[str] = Query(None),
    lang: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export wake-word records as CSV or JSON (max 100k rows, audio excluded).

    Args:
        format: Output format — 'csv' or 'json'.
        name: Filter by wake-word name.
        model: Filter by model identifier.
        plugin: Filter by plugin name.
        lang: Filter by language tag.
        db: Database session.

    Returns:
        StreamingResponse with appropriate media type.
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
    rows = q.limit(_EXPORT_ROW_CAP).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "model", "plugin", "language", "timestamp"])
        for r in rows:
            writer.writerow([r.id, r.name, r.model, r.plugin, r.language, r.timestamp])
        output.seek(0)
        return StreamingResponse(
            iter([output.read()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=wake_words.csv"},
        )
    data = [
        {
            "id": r.id,
            "name": r.name,
            "model": r.model,
            "plugin": r.plugin,
            "language": r.language,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return StreamingResponse(
        iter([json.dumps(data)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=wake_words.json"},
    )


@router.get("/utterances/export")
def export_utterances(
    format: str = Query("csv", pattern="^(csv|json)$"),
    lang: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    plugin: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export STT utterance records as CSV or JSON (max 100k rows, audio excluded).

    Args:
        format: Output format — 'csv' or 'json'.
        lang: Filter by language tag.
        model: Filter by model name.
        plugin: Filter by plugin name.
        db: Database session.

    Returns:
        StreamingResponse with appropriate media type.
    """
    q = db.query(Utterance)
    if lang:
        q = q.filter(Utterance.language == lang.lower())
    if model:
        q = q.filter(Utterance.model == model)
    if plugin:
        q = q.filter(Utterance.plugin == plugin)
    rows = q.limit(_EXPORT_ROW_CAP).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "transcript", "model", "plugin", "language", "timestamp"])
        for r in rows:
            writer.writerow(
                [r.id, r.transcript, r.model, r.plugin, r.language, r.timestamp]
            )
        output.seek(0)
        return StreamingResponse(
            iter([output.read()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=utterances.csv"},
        )
    data = [
        {
            "id": r.id,
            "transcript": r.transcript,
            "model": r.model,
            "plugin": r.plugin,
            "language": r.language,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return StreamingResponse(
        iter([json.dumps(data)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=utterances.json"},
    )
