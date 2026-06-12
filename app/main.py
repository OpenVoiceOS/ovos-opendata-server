# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""FastAPI application entry point for ovos-opendata-server."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import audio, dashboard, data_intake, export, query


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="OVOS Open Data Server",
    description="Collects anonymised voice metrics from OVOS devices.",
    version="0.1.0",
    lifespan=lifespan,
)

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
