# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Security helpers for intake endpoints: API key gate, WAV validation, rate limiting."""

from fastapi import HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def require_api_key(request: Request) -> None:
    """Dependency that enforces an API key when one is configured.

    If `get_settings().api_key` is unset, this is a no-op. Otherwise the
    request must carry a matching `X-API-Key` header.

    Raises:
        HTTPException: 401 if the configured API key is missing or wrong.
    """
    expected = get_settings().api_key
    if not expected:
        return
    if request.headers.get("X-API-Key") != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def validate_wav(data: bytes) -> None:
    """Validate that `data` looks like a WAV file (RIFF/WAVE magic bytes).

    Args:
        data: Raw audio bytes to validate.

    Raises:
        HTTPException: 400 if the bytes are not a valid WAV file.
    """
    if not (data[:4] == b"RIFF" and data[8:12] == b"WAVE"):
        raise HTTPException(status_code=400, detail="Invalid audio file")
