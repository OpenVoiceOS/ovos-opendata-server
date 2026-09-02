# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""FastAPI application entry point for ovos-opendata-server."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, get_engine
from app.routers import audio, dashboard, data_intake, export, query
from app.security import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(
    title="OVOS Open Data Server",
    description="Collects anonymised voice metrics from OVOS devices.",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting (per-IP, limit string configurable via RATE_LIMIT env var)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Register routers
app.include_router(data_intake.router)
app.include_router(query.router)
app.include_router(audio.router)
app.include_router(export.router)
app.include_router(dashboard.router)


@app.get("/status")
async def status() -> dict:
    """Health check endpoint.

    Returns:
        dict with status 'success'.
    """
    return {"status": "success"}
