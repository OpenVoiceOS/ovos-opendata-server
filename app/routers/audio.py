# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Audio streaming endpoints for wake-word and utterance samples."""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Utterance, WakeWord

router = APIRouter()


@router.get("/wake_words/{record_id}/audio")
def get_wake_word_audio(
    record_id: int,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the WAV audio for a wake-word record.

    Args:
        record_id: Primary key of the WakeWord record.
        db: Database session.

    Returns:
        StreamingResponse with media_type 'audio/wav'.

    Raises:
        HTTPException: 404 if no record with the given id exists.
    """
    row = db.query(WakeWord).filter(WakeWord.id == record_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Wake-word record not found")
    return StreamingResponse(BytesIO(row.audio), media_type="audio/wav")


@router.get("/utterances/{record_id}/audio")
def get_utterance_audio(
    record_id: int,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the WAV audio for an STT utterance record.

    Args:
        record_id: Primary key of the Utterance record.
        db: Database session.

    Returns:
        StreamingResponse with media_type 'audio/wav'.

    Raises:
        HTTPException: 404 if no record with the given id exists.
    """
    row = db.query(Utterance).filter(Utterance.id == record_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Utterance record not found")
    return StreamingResponse(BytesIO(row.audio), media_type="audio/wav")
