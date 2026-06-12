# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for dashboard stats endpoint."""

import io

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


def _seed(client: TestClient) -> None:
    client.post(
        "/intents",
        data={"utterance": "lights on", "intent": "SmartHomeSkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    client.post(
        "/intents",
        data={"utterance": "weather", "intent": "WeatherSkill", "lang": "de-de"},
        headers=OVOS_HEADERS,
    )
    audio = io.BytesIO(b"\x00" * 20)
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


def test_dashboard_stats_counts(client: TestClient) -> None:
    """Stats counts match the number of seeded records."""
    # Invalidate cache from previous tests by importing and resetting it
    from app.routers import dashboard as dash_mod
    dash_mod._stats_cache = (None, 0.0)

    _seed(client)
    dash_mod._stats_cache = (None, 0.0)  # invalidate again after seeding

    resp = client.get("/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_intents"] >= 2
    assert data["total_wake_words"] >= 1
    assert data["total_utterances"] >= 1


def test_dashboard_stats_distributions(client: TestClient) -> None:
    """Distribution dicts contain the expected keys."""
    from app.routers import dashboard as dash_mod
    dash_mod._stats_cache = (None, 0.0)

    _seed(client)
    dash_mod._stats_cache = (None, 0.0)

    resp = client.get("/dashboard/stats")
    data = resp.json()
    assert "SmartHomeSkill" in data["intent_distribution"]
    assert "en-us" in data["language_distribution"]
    assert "hey mycroft" in data["wake_word_distribution"]


def test_dashboard_html(client: TestClient) -> None:
    """GET / returns HTML dashboard page."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "OVOS" in resp.text


def test_status_endpoint(client: TestClient) -> None:
    """GET /status returns success."""
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
