# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for data intake POST endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}
BAD_HEADERS = {"User-Agent": "curl/7.0"}


def make_wav_bytes(data_size: int = 100) -> bytes:
    """Build a minimal, valid WAV file's bytes (RIFF/WAVE header + fmt/data chunks)."""
    data = b"\x00" * data_size
    fmt_chunk = b"fmt " + (16).to_bytes(4, "little") + (
        (1).to_bytes(2, "little")  # PCM
        + (1).to_bytes(2, "little")  # channels
        + (16000).to_bytes(4, "little")  # sample rate
        + (32000).to_bytes(4, "little")  # byte rate
        + (2).to_bytes(2, "little")  # block align
        + (16).to_bytes(2, "little")  # bits per sample
    )
    data_chunk = b"data" + len(data).to_bytes(4, "little") + data
    body = b"WAVE" + fmt_chunk + data_chunk
    return b"RIFF" + len(body).to_bytes(4, "little") + body


def test_intent_correct_ua(client: TestClient) -> None:
    """POST /intents with correct User-Agent returns 200."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_intent_wrong_ua(client: TestClient) -> None:
    """POST /intents with wrong User-Agent returns 404."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=BAD_HEADERS,
    )
    assert resp.status_code == 404


def test_intent_language_lowercased(client: TestClient) -> None:
    """Language tag is normalized to lowercase on ingestion."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "EN-US"},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    # Verify via query endpoint
    q = client.get("/intents?lang=en-us")
    assert q.status_code == 200
    items = q.json()["items"]
    assert any(i["language"] == "en-us" for i in items)


def test_intent_pipeline_and_core_version_stored(client: TestClient) -> None:
    """POST /intents with pipeline and core_version stores and exposes them."""
    resp = client.post(
        "/intents",
        data={
            "utterance": "turn on the lights",
            "intent": "LightsSkill.on",
            "lang": "en-us",
            "pipeline": "adapt_high|padatious_high",
            "core_version": "0.1.0",
        },
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    q = client.get("/intents?intent=LightsSkill.on")
    assert q.status_code == 200
    items = q.json()["items"]
    match = next(i for i in items if i["intent"] == "LightsSkill.on")
    assert match["pipeline"] == "adapt_high|padatious_high"
    assert match["core_version"] == "0.1.0"


def test_intent_pipeline_and_core_version_optional(client: TestClient) -> None:
    """POST /intents without pipeline/core_version still succeeds with null fields."""
    resp = client.post(
        "/intents",
        data={"utterance": "hello", "intent": "HelloSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    q = client.get("/intents?intent=HelloSkill")
    assert q.status_code == 200
    items = q.json()["items"]
    match = next(i for i in items if i["intent"] == "HelloSkill")
    assert match["pipeline"] is None
    assert match["core_version"] is None


def test_wake_word_correct_ua(client: TestClient) -> None:
    """POST /wake_word with correct User-Agent returns 200."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("test.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200


def test_wake_word_wrong_ua(client: TestClient) -> None:
    """POST /wake_word with wrong User-Agent returns 404."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us"},
        files={"audio": ("test.wav", audio, "audio/wav")},
        headers=BAD_HEADERS,
    )
    assert resp.status_code == 404


def test_wake_word_audio_too_large(client: TestClient) -> None:
    """POST /wake_word with audio exceeding MAX_AUDIO_SIZE_MB returns 413."""
    # MAX_AUDIO_SIZE_MB=1 in conftest, so 2 MB should fail
    large_audio = io.BytesIO(b"\x00" * (2 * 1024 * 1024 + 1))
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("big.wav", large_audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 413


def test_stt_correct_ua(client: TestClient) -> None:
    """POST /stt with correct User-Agent returns 200."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/stt",
        data={"transcript": "hello world", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("test.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200


def test_stt_wrong_ua(client: TestClient) -> None:
    """POST /stt with wrong User-Agent returns 404."""
    audio = io.BytesIO(make_wav_bytes())
    resp = client.post(
        "/stt",
        data={"transcript": "hello world", "lang": "en-us"},
        files={"audio": ("test.wav", audio, "audio/wav")},
        headers=BAD_HEADERS,
    )
    assert resp.status_code == 404


def test_stt_audio_too_large(client: TestClient) -> None:
    """POST /stt with audio exceeding MAX_AUDIO_SIZE_MB returns 413."""
    large_audio = io.BytesIO(b"\x00" * (2 * 1024 * 1024 + 1))
    resp = client.post(
        "/stt",
        data={"transcript": "hello", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("big.wav", large_audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 413
