# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for API key auth, WAV validation, and rate limiting on intake endpoints."""

import io
import os

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from test.test_intake import make_wav_bytes

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


@pytest.fixture(autouse=True)
def _reset_settings():
    """Ensure API_KEY/RATE_LIMIT env changes don't leak between tests."""
    yield
    os.environ.pop("API_KEY", None)
    os.environ.pop("RATE_LIMIT", None)
    get_settings.cache_clear()


def test_api_key_unset_intake_works(client: TestClient) -> None:
    """With no API_KEY configured, intake works without the header."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200


def test_api_key_set_missing_header_401(client: TestClient) -> None:
    """With API_KEY configured, a request without X-API-Key returns 401."""
    os.environ["API_KEY"] = "secret123"
    get_settings.cache_clear()
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 401


def test_api_key_set_wrong_header_401(client: TestClient) -> None:
    """With API_KEY configured, a request with the wrong X-API-Key returns 401."""
    os.environ["API_KEY"] = "secret123"
    get_settings.cache_clear()
    headers = {**OVOS_HEADERS, "X-API-Key": "wrong"}
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=headers,
    )
    assert resp.status_code == 401


def test_api_key_set_correct_header_200(client: TestClient) -> None:
    """With API_KEY configured, a request with the correct X-API-Key returns 200."""
    os.environ["API_KEY"] = "secret123"
    get_settings.cache_clear()
    headers = {**OVOS_HEADERS, "X-API-Key": "secret123"}
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=headers,
    )
    assert resp.status_code == 200


def test_wake_word_bad_magic_bytes_400(client: TestClient) -> None:
    """POST /wake_word with non-WAV bytes returns 400."""
    audio = io.BytesIO(b"not a wav file at all")
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("bad.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 400


def test_stt_bad_magic_bytes_400(client: TestClient) -> None:
    """POST /stt with non-WAV bytes returns 400."""
    audio = io.BytesIO(b"not a wav file at all")
    resp = client.post(
        "/stt",
        data={"transcript": "hello", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("bad.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 400


def test_wake_word_valid_wav_accepted(client: TestClient) -> None:
    """POST /wake_word with a valid minimal WAV header is accepted."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("good.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200


def test_stt_valid_wav_accepted(client: TestClient) -> None:
    """POST /stt with a valid minimal WAV header is accepted."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/stt",
        data={"transcript": "hello", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("good.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200


def test_rate_limit_exceeded_returns_429(client: TestClient) -> None:
    """The third request within a 2/minute limit returns 429."""
    os.environ["RATE_LIMIT"] = "2/minute"
    get_settings.cache_clear()

    def _post():
        return client.post(
            "/intents",
            data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
            headers=OVOS_HEADERS,
        )

    assert _post().status_code == 200
    assert _post().status_code == 200
    assert _post().status_code == 429


def test_user_agent_gate_still_enforced(client: TestClient) -> None:
    """Wrong User-Agent still returns 404, independent of API key/rate limit."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers={"User-Agent": "curl/7.0"},
    )
    assert resp.status_code == 404
