# ovos-opendata-server

FastAPI service that collects anonymised OVOS usage metrics — wake-word samples, STT utterances, and intent matches — from community devices. Data is stored in PostgreSQL and browsable through the built-in web dashboard.

## Navigation

| Document | Description |
|----------|-------------|
| [api-reference.md](api-reference.md) | All endpoints, params, response schemas |
| [dashboard.md](dashboard.md) | Web dashboard usage guide |

## Quick Start

```bash
cp .env.example .env        # fill in credentials
docker compose up --build -d
# API: http://localhost:8007
# Dashboard: http://localhost:8007/
```

## Architecture

- `app/main.py` — FastAPI app + lifespan (table creation)
- `app/database.py` — SQLAlchemy engine, `get_db()` dependency
- `app/models.py` — `Intent`, `WakeWord`, `Utterance` ORM models; language normalised via `@validates`
- `app/schemas.py` — Pydantic v2 response schemas
- `app/routers/data_intake.py` — POST endpoints (User-Agent gate, audio size limit)
- `app/routers/query.py` — paginated GET list endpoints
- `app/routers/audio.py` — audio streaming endpoints
- `app/routers/export.py` — CSV/JSON bulk export
- `app/routers/dashboard.py` — stats aggregation + HTML dashboard

## Authentication

All intake endpoints require `User-Agent: ovos-metrics`. Any other value returns `404` (intentional, not `403`).

## Configuration

All configuration via environment variables. See `.env.example`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL DSN; `RuntimeError` if unset |
| `MAX_AUDIO_SIZE_MB` | No | `10` | Maximum audio upload size |
