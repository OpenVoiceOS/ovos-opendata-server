# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""Dashboard stats and HTML rendering endpoints."""

import time
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Intent, Utterance, WakeWord
from app.schemas import DashboardStats

router = APIRouter()

_templates: Optional[Jinja2Templates] = None

# Module-level stats cache: (stats_dict, expire_timestamp)
_stats_cache: Tuple[Optional[Dict[str, Any]], float] = (None, 0.0)


def _get_templates() -> Jinja2Templates:
    """Return the Jinja2Templates instance (lazily initialized)."""
    global _templates
    if _templates is None:
        import os

        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        _templates = Jinja2Templates(directory=templates_dir)
    return _templates


def _compute_stats(db: Session) -> Dict[str, Any]:
    """Run aggregation queries and return a stats dict.

    Args:
        db: Database session.

    Returns:
        Dict suitable for constructing DashboardStats.
    """
    total_intents = db.query(func.count(Intent.id)).scalar() or 0
    total_wake_words = db.query(func.count(WakeWord.id)).scalar() or 0
    total_utterances = db.query(func.count(Utterance.id)).scalar() or 0

    intent_dist: Dict[str, int] = {}
    for intent_name, count in db.query(Intent.intent, func.count(Intent.id)).group_by(Intent.intent).all():
        intent_dist[intent_name] = count

    lang_dist: Dict[str, int] = {}
    for lang, count in db.query(Intent.language, func.count(Intent.id)).group_by(Intent.language).all():
        if lang:
            lang_dist[lang] = count

    ww_dist: Dict[str, int] = {}
    for name, count in db.query(WakeWord.name, func.count(WakeWord.id)).group_by(WakeWord.name).all():
        if name:
            ww_dist[name] = count

    return {
        "total_intents": total_intents,
        "total_wake_words": total_wake_words,
        "total_utterances": total_utterances,
        "intent_distribution": intent_dist,
        "language_distribution": lang_dist,
        "wake_word_distribution": ww_dist,
    }


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    """Return aggregated statistics for the dashboard, cached for 60 seconds.

    Args:
        db: Database session.

    Returns:
        DashboardStats with counts and distribution dicts.
    """
    global _stats_cache
    cached, expires = _stats_cache
    if cached is None or time.monotonic() > expires:
        cached = _compute_stats(db)
        _stats_cache = (cached, time.monotonic() + get_settings().dashboard_cache_ttl)
    return DashboardStats(**cached)


@router.get("/", response_class=HTMLResponse)
def dashboard_html(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the dashboard HTML page.

    Args:
        request: FastAPI request object.
        db: Database session.

    Returns:
        HTMLResponse with rendered dashboard.html template.
    """
    templates = _get_templates()
    return templates.TemplateResponse(request, "dashboard.html")
