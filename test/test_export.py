# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for CSV/JSON export endpoints."""

import csv
import io
import json

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


def _seed(client: TestClient) -> None:
    client.post(
        "/intents",
        data={"utterance": "lights on", "intent": "SmartHomeSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    audio = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    client.post(
        "/wake_word",
        data={"name": "hey mycroft", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )
    audio.seek(0)
    client.post(
        "/stt",
        data={"transcript": "play music", "lang": "en-us", "model": "m", "plugin": "p"},
        files={"audio": ("t.wav", audio, "audio/wav")},
        headers=OVOS_HEADERS,
    )


def test_intents_export_csv(client: TestClient) -> None:
    """GET /intents/export?format=csv returns CSV with correct columns."""
    _seed(client)
    resp = client.get("/intents/export?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    reader = csv.DictReader(io.StringIO(resp.text))
    assert "intent" in reader.fieldnames
    assert "language" in reader.fieldnames
    rows = list(reader)
    assert len(rows) >= 1


def test_intents_export_json(client: TestClient) -> None:
    """GET /intents/export?format=json returns JSON array."""
    _seed(client)
    resp = client.get("/intents/export?format=json")
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "intent" in data[0]


def test_intents_export_filter(client: TestClient) -> None:
    """Export respects lang filter."""
    _seed(client)
    # Add a German record
    client.post(
        "/intents",
        data={"utterance": "licht an", "intent": "SmartHomeSkill", "lang": "de-de"},
        headers=OVOS_HEADERS,
    )
    resp = client.get("/intents/export?format=csv&lang=de-de")
    assert resp.status_code == 200
    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        assert row["language"] == "de-de"


def test_wake_words_export_csv(client: TestClient) -> None:
    """GET /wake_words/export?format=csv returns CSV with correct columns."""
    _seed(client)
    resp = client.get("/wake_words/export?format=csv")
    assert resp.status_code == 200
    reader = csv.DictReader(io.StringIO(resp.text))
    assert "name" in reader.fieldnames


def test_wake_words_export_json(client: TestClient) -> None:
    """GET /wake_words/export?format=json returns JSON array."""
    _seed(client)
    resp = client.get("/wake_words/export?format=json")
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert isinstance(data, list)


def test_utterances_export_csv(client: TestClient) -> None:
    """GET /utterances/export?format=csv returns CSV with correct columns."""
    _seed(client)
    resp = client.get("/utterances/export?format=csv")
    assert resp.status_code == 200
    reader = csv.DictReader(io.StringIO(resp.text))
    assert "transcript" in reader.fieldnames


def test_utterances_export_json(client: TestClient) -> None:
    """GET /utterances/export?format=json returns JSON array."""
    _seed(client)
    resp = client.get("/utterances/export?format=json")
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert isinstance(data, list)
