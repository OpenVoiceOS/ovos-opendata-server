# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for audio streaming endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


def _upload_ww(client: TestClient) -> int:
    """Upload a wake-word sample and return its ID."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    resp = client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    # Retrieve the id by listing
    items = client.get("/wake_words").json()["items"]
    return items[0]["id"]


def _upload_utt(client: TestClient) -> int:
    """Upload an STT utterance and return its ID."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    resp = client.post(
        "/stt",
        data={"transcript": "hello", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    assert resp.status_code == 200
    items = client.get("/utterances").json()["items"]
    return items[0]["id"]


def test_wake_word_audio_stream(client: TestClient) -> None:
    """GET /wake_words/{id}/audio returns 200 with audio/wav content type."""
    ww_id = _upload_ww(client)
    resp = client.get(f"/wake_words/{ww_id}/audio")
    assert resp.status_code == 200
    assert "audio/wav" in resp.headers["content-type"]


def test_wake_word_audio_missing(client: TestClient) -> None:
    """GET /wake_words/{id}/audio returns 404 for unknown id."""
    resp = client.get("/wake_words/99999/audio")
    assert resp.status_code == 404


def test_utterance_audio_stream(client: TestClient) -> None:
    """GET /utterances/{id}/audio returns 200 with audio/wav content type."""
    utt_id = _upload_utt(client)
    resp = client.get(f"/utterances/{utt_id}/audio")
    assert resp.status_code == 200
    assert "audio/wav" in resp.headers["content-type"]


def test_utterance_audio_missing(client: TestClient) -> None:
    """GET /utterances/{id}/audio returns 404 for unknown id."""
    resp = client.get("/utterances/99999/audio")
    assert resp.status_code == 404
