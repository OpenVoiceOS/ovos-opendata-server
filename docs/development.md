# Contributor Guide

Working on the server itself, rather than running or connecting to it. Start
here for repo layout, running from source, tests, and how a schema change
flows end to end.

## Repo layout

```
app/
  main.py           FastAPI app, lifespan (table creation), router wiring
  config.py         pydantic-settings Settings, env-var driven
  database.py       lazy SQLAlchemy engine/session, Base, get_db() dependency
  models.py         Intent, WakeWord, Utterance ORM models
  schemas.py        Pydantic v2 response schemas
  routers/
    data_intake.py  POST /intents, /wake_word, /stt
    query.py        GET /intents, /wake_words, /utterances (paginated)
    audio.py        GET /wake_words/{id}/audio, /utterances/{id}/audio
    export.py       GET .../export (CSV/JSON bulk)
    dashboard.py    GET /dashboard/stats, GET / (HTML dashboard)
  templates/
    dashboard.html  Jinja2 template for the dashboard page
  static/
    css/, js/       Dashboard frontend assets
migrations/         Alembic environment and revisions
scripts/
  entrypoint.sh     Container entrypoint: `alembic upgrade head` then uvicorn
  populate_*.py     Local demo-data / dataset-import helpers
test/               pytest suite, mirrors app/ structure
```

## Run from source

```bash
git clone https://github.com/OpenVoiceOS/ovos-opendata-server
cd ovos-opendata-server
uv venv
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload
```

With no environment variables set, the app falls back to a local SQLite file
(`ovos_opendata.db`) and creates tables automatically on startup — no
migration step needed for local development. Set `DATABASE_URL` if you want
to develop against Postgres instead.

## Run the tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest test/ -v --cov=app --cov-report=term-missing
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` avoids autoloading pytest plugins that
aren't relevant here and can otherwise interfere with collection in some
environments — set it whenever you invoke pytest directly in this repo.

### Test layout

Tests live under `test/`, one file per concern, mirroring the app:

- `test_config.py` — settings loading and defaults
- `test_intake.py` — POST endpoint behavior (validation, error codes)
- `test_query.py` — paginated list endpoints and filters
- `test_export.py` — CSV/JSON export
- `test_audio.py` — audio streaming
- `test_dashboard_stats.py` — stats aggregation and caching
- `test_migrations.py` — Alembic revisions apply cleanly

`test/conftest.py` sets `DATABASE_URL` to a throwaway SQLite file **before**
any `app` module is imported (settings are read once, at import time, via
`lru_cache`), builds tables directly with `Base.metadata.create_all()`, and
overrides the `get_db` dependency so every test hits that isolated database.
Each test gets a clean database via an autouse fixture that truncates all
tables afterward.

## How migrations work

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/).

- In production and in the Docker image, `scripts/entrypoint.sh` runs
  `alembic upgrade head` automatically before starting the server — you never
  run this by hand there.
- In local development, the app also calls `Base.metadata.create_all()` on
  startup for convenience, so a fresh SQLite database works immediately
  without running migrations. This means `models.py` and the latest
  migration head must always describe the same schema — if they drift, fresh
  installs (metadata-created) and upgraded installs (migration-created) would
  disagree.

To apply migrations manually against a database:

```bash
alembic upgrade head
```

## Adding a field, end to end

Say you want to add a `device_id` field to intent uploads. The change touches
five places, in this order:

1. **Model** (`app/models.py`) — add the column to `Intent`:

   ```python
   device_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
   ```

2. **Schema** (`app/schemas.py`) — expose it on `IntentRecord` if it should be
   readable via the API:

   ```python
   device_id: Optional[str] = None
   ```

3. **Intake** (`app/routers/data_intake.py`) — accept it on `POST /intents`
   and pass it through to the model:

   ```python
   device_id: str = Form(None),
   ...
   record = Intent(..., device_id=device_id)
   ```

4. **Export/query** (`app/routers/query.py`, `app/routers/export.py`) —
   include it in the `IntentRecord(...)` construction in `query.py`, and in
   both the CSV header/row and JSON dict in `export.py`, if you want it
   queryable and exportable.

5. **Migration** — generate and review a revision:

   ```bash
   alembic revision --autogenerate -m "add device_id to intents"
   ```

   Autogenerate diffs `models.py` against the current migration head and
   writes `upgrade()`/`downgrade()` for you (see
   `migrations/versions/0002_intent_pipeline_metadata.py` for a real example
   that adds two nullable string columns). Always read the generated file —
   autogenerate doesn't always get data migrations, renames, or
   type-narrowing changes right — then commit it alongside the code change.

Finally, update `docs/api-reference.md` and `docs/datasets.md` if the field
is part of the public contract, and add or extend a test in `test/`.

## CI overview

Workflows live in `.github/workflows/` and mostly call shared, reusable
workflows from `OpenVoiceOS/gh-automations`, triggered on pushes and PRs
against `dev`:

- **Build Tests** (`build-tests.yml`) — installs the `dev` extra and runs the
  `test/` suite.
- **Lint** (`lint.yml`) — standard OVOS lint checks.
- **License Check** (`license-check.yml`) — scans dependency licenses;
  `psycopg2-binary` is explicitly excluded from the copyleft fail set since
  it's used only as a database driver library, not modified or redistributed.
- **Pip Audit** (`pip-audit.yml`) — scans dependencies for known
  vulnerabilities.
- **Publish Docker Image** (`publish-docker.yml`) — on version tags (`v*`) or
  manual dispatch, builds and pushes a multi-arch (amd64/arm64) image to
  `ghcr.io/openvoiceos/ovos-opendata-server`.

## Code style

- Type hints throughout; ORM models use SQLAlchemy 2.0's `Mapped[...]` style.
- Docstrings on public functions describe args, return value, and raised
  exceptions — follow the existing pattern in `app/routers/`.
- Keep endpoint handlers thin: validation and DB access inline is fine at
  this size, but push shared logic (like `read_audio_with_limit`) into a
  helper function rather than duplicating it across routers.
- Settings only ever come from `app.config.get_settings()` — don't read
  `os.environ` directly elsewhere in the app.
