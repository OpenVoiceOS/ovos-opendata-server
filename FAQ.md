# FAQ — ovos-opendata-server

## What is ovos-opendata-server?
A FastAPI service that collects anonymised OVOS device metrics (wake-word audio, STT utterances, intent matches) into PostgreSQL for open dataset building.

## How do I run it?
```bash
cp .env.example .env
docker compose up --build -d
```
API on port 8007, dashboard at `http://localhost:8007/`.

## Why does DATABASE_URL raise RuntimeError if not set?
Hardcoded credentials are a security risk. The service refuses to start without an explicit DATABASE_URL. See `.env.example`.

## Why do intake endpoints return 404 for unknown clients?
The `User-Agent: ovos-metrics` check returns 404 (not 403) intentionally to avoid discoverability of the write API.

## How is language normalised?
All three ORM models have `@validates("language")` that lowercases and strips the value on write — `app/models.py:32`, `app/models.py:56`, `app/models.py:80`.

## What is the audio size limit?
Controlled by `MAX_AUDIO_SIZE_MB` (default 10). Exceeding it returns `413`. — `app/routers/data_intake.py:read_audio_with_limit`.

## Does the list API include audio bytes?
No. Audio is excluded from `/intents`, `/wake_words`, and `/utterances`. Use `/wake_words/{id}/audio` or `/utterances/{id}/audio` to stream individual files.

## How do I export data?
`GET /intents/export?format=csv` or `?format=json`. Same for `/wake_words/export` and `/utterances/export`. Hard cap: 100k rows.

## How are dashboard stats cached?
Module-level dict in `app/routers/dashboard.py` with a 60-second TTL. — `_stats_cache` at module level.

## How do I run tests?
```bash
uv run pytest test/ -v --cov=app --cov-report=term-missing
```
