# ovos-opendata-server

FastAPI service that collects anonymised OVOS device metrics — intent matches, wake-word samples, and STT utterances — into PostgreSQL for open dataset building, with a web dashboard and CSV/JSON export.

## Setup

```bash
uv pip install -e ".[dev]"
```

Requires `DATABASE_URL` (PostgreSQL DSN) in the environment or `.env` — `app/database.py` raises `RuntimeError` at import time if it is unset. Copy `.env.example` to `.env` first. Optional `MAX_AUDIO_SIZE_MB` (default `10`) caps audio uploads.

Run the service locally with `docker compose up --build -d` (API on `:8007`) or `uvicorn app.main:app`.

## Test

```bash
uv run pytest test/ -v --cov=app --cov-report=term-missing
```

Tests use FastAPI's TestClient over an in-memory/SQLite test database (see `test/conftest.py`); no live PostgreSQL needed. `conftest.py` sets `DATABASE_URL` before app import.

## Lint/Typecheck

Lint runs in CI via the gh-automations `lint.yml` reusable workflow; no project-local lint config is committed.

## Layout

- `app/main.py` — FastAPI app factory, lifespan creates tables, registers routers, `/status` health check.
- `app/database.py` — SQLAlchemy engine/session, `get_db` dependency, reads `DATABASE_URL`.
- `app/models.py` — ORM models `Intent`, `WakeWord` (table `wake_words`), `Utterance` (table `stt`); each normalises `language` to lowercase via a validator. Audio stored as `LargeBinary`.
- `app/schemas.py` — Pydantic schemas.
- `app/routers/` — `data_intake` (POST `/intents`, `/wake_word`, `/stt`, gated by `require_ovos_agent`), `query` (paginated GET lists), `audio` (stream stored audio), `export` (CSV/JSON), `dashboard` (stats + HTML, 60s cache).
- `dashboard/dashboard.py` — separate dashboard component (`Dockerfile.dashboard`).
- `scripts/` — `populate_db.py`, `populate_utt.py`, `populate_ww.py` seed/dev helpers.
- `test/` — pytest suite per router.
- `docs/` — `api-reference.md`, `dashboard.md`, `index.md`.

This is a standalone web service, not a Python plugin/skill — it declares no entry points.

Auth: all intake POST endpoints require header `User-Agent: ovos-metrics`; `require_ovos_agent` returns 404 (not 403) on mismatch to avoid endpoint discovery.

## Conventions

- Branches: work on `dev`, stable on `master`. NEVER use `main`.
- Never edit a version field by hand — gh-automations bumps semver from conventional-commit prefixes (`feat:`, `fix:`, `feat!:`).
- New repos are private by default; do not make source public without asking.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- Reference `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary in docs/commits/code (no history, no dates, no "design mistake" narration) — describe current state only.
- CI is provided by `OpenVoiceOS/gh-automations` reusable workflows.

## Gotchas

- `app/database.py` evaluates `DATABASE_URL` at module import, so any import of `app.*` fails fast without it set — tests set it in `conftest.py`.
- Tables are auto-created on app startup via the lifespan hook (`Base.metadata.create_all`); there is no migration tooling.
- Audio for wake words and utterances is stored inline as `LargeBinary` in PostgreSQL.
- The working tree carries untracked scratch artifacts (`.coverage`, `ovos_opendata_server.egg-info/`, and `AUDIT.md`/`MAINTENANCE_REPORT.md`/`SUGGESTIONS.md`/`QUICK_FACTS.md`/`FAQ.md`); only `README.md` and `privacy.md` are tracked. Do not commit the scratch files.
