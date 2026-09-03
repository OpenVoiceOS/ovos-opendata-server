# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Tests for dashboard stats endpoint."""

import io

import pytest
from fastapi.testclient import TestClient

OVOS_HEADERS = {"User-Agent": "ovos-metrics"}


def _make_wav_bytes(data_size: int = 20) -> bytes:
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
    audio = io.BytesIO(_make_wav_bytes())
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


def test_dashboard_stats_session_distribution(client: TestClient) -> None:
    """session_distribution buckets intents by session_default true/false/unknown."""
    from app.routers import dashboard as dash_mod
    dash_mod._stats_cache = (None, 0.0)

    client.post(
        "/intents",
        data={
            "utterance": "local one",
            "intent": "LocalSkill",
            "lang": "en-us",
            "session_default": "true",
        },
        headers=OVOS_HEADERS,
    )
    client.post(
        "/intents",
        data={
            "utterance": "remote one",
            "intent": "RemoteSkill",
            "lang": "en-us",
            "session_default": "false",
        },
        headers=OVOS_HEADERS,
    )
    client.post(
        "/intents",
        data={"utterance": "legacy one", "intent": "LegacySkill", "lang": "en-us"},
        headers=OVOS_HEADERS,
    )
    dash_mod._stats_cache = (None, 0.0)

    resp = client.get("/dashboard/stats")
    assert resp.status_code == 200
    dist = resp.json()["session_distribution"]
    assert dist["true"] >= 1
    assert dist["false"] >= 1
    assert dist["unknown"] >= 1


def test_dashboard_html(client: TestClient) -> None:
    """GET / returns HTML dashboard page."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "OVOS" in resp.text


def test_dashboard_html_expected_elements(client: TestClient) -> None:
    """GET / includes the expected card, tab, and footer element ids."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.text
    for element_id in (
        "stat-intents",
        "stat-wakewords",
        "stat-utterances",
        "tab-btn-intents",
        "tab-btn-wakewords",
        "tab-btn-utterances",
        "dashboard-footer",
    ):
        assert f'id="{element_id}"' in body


def test_dashboard_html_no_cdn_or_inline_handlers(client: TestClient) -> None:
    """GET / does not load Chart.js from a CDN and has no inline onclick handlers."""
    resp = client.get("/")
    body = resp.text
    assert "cdn.jsdelivr" not in body
    assert "onclick=" not in body


def test_dashboard_html_strapline_and_privacy_link(client: TestClient) -> None:
    """GET / states what the site is and links the privacy policy near the heading."""
    resp = client.get("/")
    body = resp.text
    assert "opt-in" in body.lower()
    assert "anonymised" in body.lower()
    assert "privacy.md" in body


def test_dashboard_html_no_duplicate_session_caption(client: TestClient) -> None:
    """#card-session carries its caption on the canvas (aria-label), not in a separate <p> too."""
    resp = client.get("/")
    body = resp.text
    session_card = body[body.index('id="card-session"'):body.index('id="card-session"') + 400]
    assert "<p class=\"card-label\">" not in session_card
    assert "Local vs remote (HiveMind) clients" in session_card


def test_dashboard_html_accessibility_attributes(client: TestClient) -> None:
    """GET / carries the expected ARIA roles for status regions, charts, and the modal."""
    resp = client.get("/")
    body = resp.text
    assert body.count('role="status"') >= 4
    assert body.count('role="img"') == 4
    assert 'role="dialog"' in body
    assert 'aria-modal="true"' in body
    assert "<h2" in body


def test_dashboard_vendored_chartjs_served(client: TestClient) -> None:
    """The vendored Chart.js UMD build is served from /static."""
    resp = client.get("/static/js/vendor/chart.umd.min.js")
    assert resp.status_code == 200
    assert "Chart" in resp.text


def test_status_endpoint(client: TestClient) -> None:
    """GET /status returns success."""
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_dashboard_redirect(client: TestClient) -> None:
    """GET /dashboard redirects to /dashboard/stats."""
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"].endswith("/dashboard/stats")


def test_dashboard_slash_redirect(client: TestClient) -> None:
    """GET /dashboard/ redirects to /dashboard/stats."""
    resp = client.get("/dashboard/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"].endswith("/dashboard/stats")
