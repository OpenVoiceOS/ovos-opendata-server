# Documentation

ovos-opendata-server collects opt-in telemetry from OVOS voice devices —
wake-word audio, STT utterances, intent matches — and turns it into open,
reusable datasets. Pick the guide that matches what you're trying to do.

## Choose your path

**I run an OVOS device and want to contribute data.**
Read [connecting-devices.md](connecting-devices.md) for `mycroft.conf`
examples, an exact list of what gets uploaded (and what never leaves the
device), and how to verify it's working or turn it off again.

**I want to host my own server.**
Read [self-hosting.md](self-hosting.md) for the architecture, a production
Docker Compose setup with Postgres, the full environment variable reference,
TLS, backups, and upgrades. Start with [getting-started.md](getting-started.md)
first if you just want to try it locally before going to production.

**I want to use the data.**
Read [datasets.md](datasets.md) for how to pull CSV/JSON exports, stream
individual audio files, what each column means, and notes on building
wake-word or STT training sets. See also [privacy.md](../privacy.md) for the
licensing and ethics behind the data.

**I want to hack on the code.**
Read [development.md](development.md) for the repo layout, running from
source, the test suite, and how to add a new field end to end (model, schema,
intake endpoint, export, migration).

## All guides

| Document | Description |
|----------|-------------|
| [getting-started.md](getting-started.md) | Run the server locally in minutes, seed demo data, make your first API call |
| [connecting-devices.md](connecting-devices.md) | Point an OVOS device at a server, understand exactly what is uploaded |
| [self-hosting.md](self-hosting.md) | Production deployment, environment variables, trust model, backups |
| [api-reference.md](api-reference.md) | Every endpoint, parameter, and response code |
| [datasets.md](datasets.md) | Exporting and using the collected data |
| [development.md](development.md) | Contributor guide: layout, tests, migrations, CI |
| [dashboard.md](dashboard.md) | Web dashboard usage guide |
| [../FAQ.md](../FAQ.md) | Short answers to common questions |
| [../privacy.md](../privacy.md) | What is collected, why, and your choices |

## Architecture at a glance

- `app/main.py` — FastAPI app, table creation on startup, router wiring
- `app/config.py` — environment-driven settings (`pydantic-settings`)
- `app/database.py` — lazy SQLAlchemy engine, `get_db()` dependency
- `app/models.py` — `Intent`, `WakeWord`, `Utterance` ORM models; language
  normalized to lowercase via `@validates`
- `app/schemas.py` — Pydantic v2 response schemas
- `app/routers/data_intake.py` — POST endpoints devices upload to (User-Agent
  gate, optional API key, audio size and format checks, rate limiting)
- `app/routers/query.py` — paginated GET list endpoints
- `app/routers/audio.py` — audio streaming endpoints
- `app/routers/export.py` — CSV/JSON bulk export
- `app/routers/dashboard.py` — stats aggregation + HTML dashboard

A deeper walkthrough is in [self-hosting.md](self-hosting.md) (operators) and
[development.md](development.md) (contributors).
