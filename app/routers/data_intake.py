# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Data intake POST endpoints for OVOS device metrics collection."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Intent, Utterance, WakeWord

router = APIRouter()


def require_ovos_agent(request: Request) -> None:
    """Dependency that rejects requests without the OVOS metrics User-Agent.

    Raises HTTPException 404 for any client not sending 'ovos-metrics' as User-Agent.
    This intentionally returns 404 (not 403) to avoid discoverability.
    """
    if request.headers.get("User-Agent", "").lower() != "ovos-metrics":
        raise HTTPException(status_code=404)


async def read_audio_with_limit(audio: UploadFile) -> bytes:
    """Read audio file bytes, raising 413 if the file exceeds MAX_AUDIO_SIZE_MB.

    Args:
        audio: The uploaded audio file.

    Returns:
        Raw audio bytes.

    Raises:
        HTTPException: 413 if the file exceeds the configured size limit.
    """
    max_bytes = get_settings().max_audio_size_mb * 1024 * 1024
    data = await audio.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Audio file too large")
    return data


@router.post("/intents")
async def upload_intent(
    request: Request,
    utterance: str = Form(...),
    intent: str = Form(...),
    lang: str = Form(...),
    match_data: str = Form(None),
    pipeline: str = Form(None),
    core_version: str = Form(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_ovos_agent),
) -> dict:
    """Record an intent match event from an OVOS device.

    Args:
        request: FastAPI request (used by require_ovos_agent dependency).
        utterance: The user utterance text.
        intent: The matched intent name.
        lang: BCP-47 language tag (will be normalized to lowercase).
        match_data: Optional JSON string of intent match details.
        pipeline: Optional pipe-joined string of pipeline stages that were
            attempted before this intent matched (e.g. "adapt_high|padatious_high").
        core_version: Optional ovos-core version string of the reporting device.
        db: Database session.
        _: require_ovos_agent dependency result (unused).

    Returns:
        dict with status 'success'.
    """
    record = Intent(
        utterance=utterance,
        intent=intent,
        language=lang,
        match_data=match_data,
        pipeline=pipeline,
        core_version=core_version,
    )
    db.add(record)
    db.commit()
    return {"status": "success"}


@router.post("/wake_word")
async def upload_wake_word(
    request: Request,
    name: str = Form(...),
    audio: UploadFile = File(...),
    model: str = Form(None),
    lang: str = Form(None),
    plugin: str = Form(None),
    plugin_config: str = Form(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_ovos_agent),
) -> dict:
    """Record a wake-word detection sample from an OVOS device.

    Args:
        request: FastAPI request.
        name: Wake-word name (e.g. 'hey mycroft').
        audio: WAV audio file of the detection.
        model: Model filename or identifier.
        lang: BCP-47 language tag.
        plugin: Plugin module name.
        plugin_config: Optional JSON plugin configuration.
        db: Database session.
        _: require_ovos_agent dependency result (unused).

    Returns:
        dict with status 'success'.
    """
    audio_bytes = await read_audio_with_limit(audio)
    record = WakeWord(
        name=name,
        language=lang,
        model=model,
        plugin=plugin,
        plugin_config=plugin_config,
        audio=audio_bytes,
    )
    db.add(record)
    db.commit()
    return {"status": "success"}


@router.post("/stt")
async def upload_stt_utterance(
    request: Request,
    transcript: str = Form(...),
    lang: str = Form(...),
    audio: UploadFile = File(...),
    model: str = Form(None),
    plugin: str = Form(None),
    plugin_config: str = Form(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_ovos_agent),
) -> dict:
    """Record an STT utterance sample from an OVOS device.

    Args:
        request: FastAPI request.
        transcript: Transcribed text of the utterance.
        lang: BCP-47 language tag.
        audio: WAV audio file of the utterance.
        model: STT model name.
        plugin: STT plugin module name.
        plugin_config: Optional JSON plugin configuration.
        db: Database session.
        _: require_ovos_agent dependency result (unused).

    Returns:
        dict with status 'success'.
    """
    audio_bytes = await read_audio_with_limit(audio)
    record = Utterance(
        transcript=transcript,
        language=lang,
        model=model,
        plugin=plugin,
        plugin_config=plugin_config,
        audio=audio_bytes,
    )
    db.add(record)
    db.commit()
    return {"status": "success"}
