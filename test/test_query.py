# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for paginated query endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


def _seed_intents(client: TestClient, count: int = 5) -> None:
    for i in range(count):
        lang = "en-us" if i % 2 == 0 else "de-de"
        client.post(
            "/intents",
            data={"utterance": f"utterance {i}", "intent": f"Skill{i}", "lang": lang},
            headers=OVOS_HEADERS,
        )


def test_intents_pagination(client: TestClient) -> None:
    """Pagination limit and page params return correct subsets."""
    _seed_intents(client, 10)
    resp = client.get("/intents?page=1&limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["limit"] == 3
    assert data["total"] >= 10


def test_intents_filter_lang(client: TestClient) -> None:
    """Language filter returns only records for that language."""
    _seed_intents(client, 6)
    resp = client.get("/intents?lang=en-us")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["language"] == "en-us"


def test_intents_filter_intent(client: TestClient) -> None:
    """Intent filter returns only records matching exact intent name."""
    _seed_intents(client, 5)
    resp = client.get("/intents?intent=Skill0")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["intent"] == "Skill0"


def test_intents_filter_date(client: TestClient) -> None:
    """date_from/date_to filters are accepted without error."""
    _seed_intents(client, 2)
    resp = client.get("/intents?date_from=2020-01-01T00:00:00&date_to=2099-01-01T00:00:00")
    assert resp.status_code == 200


def test_wake_words_list(client: TestClient) -> None:
    """GET /wake_words returns valid paginated response."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    client.post(
        "/wake_word",
        data={"name": "hey test", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    resp = client.get("/wake_words")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["items"][0].get("wake_word") is not None


def test_wake_words_filter_name(client: TestClient) -> None:
    """name filter on /wake_words narrows results."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    client.post(
        "/wake_word",
        data={"name": "unique-ww", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    resp = client.get("/wake_words?name=unique-ww")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["wake_word"] == "unique-ww"


def test_utterances_list(client: TestClient) -> None:
    """GET /utterances returns valid paginated response."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    client.post(
        "/stt",
        data={"transcript": "hi there", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    resp = client.get("/utterances")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


def test_utterances_filter_lang(client: TestClient) -> None:
    """lang filter on /utterances returns only matching records."""
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    client.post(
        "/stt",
        data={"transcript": "bonjour", "lang": "fr-fr", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    resp = client.get("/utterances?lang=fr-fr")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["language"] == "fr-fr"
