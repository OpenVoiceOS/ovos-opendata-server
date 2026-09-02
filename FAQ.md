# FAQ — ovos-opendata-server

## What is ovos-opendata-server?

A FastAPI service that collects opt-in OVOS device metrics (wake-word audio,
STT utterances, intent matches) into a database for open dataset building. See
[docs/index.md](docs/index.md) for the full documentation.

## Is my voice recorded?

Only if you explicitly opt into wake-word (`ww_urls`) or STT (`stt_urls`)
uploads in your device's `mycroft.conf`. By default, nothing is uploaded at
all. If you only enable `intent_urls`, the server receives text (the
utterance and matched intent) and never any audio. See
[docs/connecting-devices.md](docs/connecting-devices.md) for exactly what
each upload contains, and [privacy.md](privacy.md) for the full policy.

## Can I run my own server?

Yes — that's a first-class use case, not an afterthought. See
[docs/self-hosting.md](docs/self-hosting.md) for a production Docker Compose
setup, or [docs/getting-started.md](docs/getting-started.md) to try it
locally first. Point your device's `open_data` config at your own instance
instead of (or in addition to) the public one, and your data never leaves
your network.

## How do I run it?

```bash
cp .env.example .env
docker compose up --build -d
```

API on port `8007`, dashboard at `http://localhost:8007/`. Full walkthrough:
[docs/getting-started.md](docs/getting-started.md).

## What does DATABASE_URL default to, and what should I use in production?

If unset, the server falls back to a local SQLite file
(`sqlite:///./ovos_opendata.db`) so it's importable and runnable with zero
configuration for local development and tests. **Production deployments
should always set `DATABASE_URL` to a PostgreSQL DSN** — SQLite doesn't
handle concurrent writers well and isn't a good fit once devices are actively
uploading. See [docs/self-hosting.md](docs/self-hosting.md).

## Why do intake endpoints return 404 for unknown clients?

The `User-Agent: ovos-metrics` check returns `404` (not `403`) intentionally,
to avoid making the write API discoverable to casual scanners or browsers
poking at the URL.

## What's the GDPR / data-deletion story?

No personally identifiable information is collected by design — see
[privacy.md](privacy.md). Because uploads aren't tied to any account or
verifiable identity, the server has no way to confirm who submitted a given
record, so individual submitted records generally can't be deleted on
request. If you need guaranteed control over your data, run your own server
(see above) — you control deletion there directly, since it's your database.

## How is language normalized?

All three record types lowercase and strip the `language`/`lang` value on
write (`app/models.py`), so `"En-US"` and `"en-us "` both end up stored and
queryable as `"en-us"`.

## What is the audio size limit?

Controlled by `MAX_AUDIO_SIZE_MB` (default 10). Exceeding it returns `413`.

## Are uploads validated?

Yes. Wake-word and STT audio must be a real WAV file (checked by its
RIFF/WAVE header) or the upload is rejected with `400`. If the server has
`API_KEY` configured, uploads also need a matching `X-API-Key` header or they
get `401`. All intake endpoints are rate limited per IP (`RATE_LIMIT`,
default `60/minute`; exceeding it returns `429`).

## Does the list API include audio bytes?

No. Audio is excluded from `/intents`, `/wake_words`, and `/utterances`. Use
`/wake_words/{id}/audio` or `/utterances/{id}/audio` to stream individual
files.

## How do I get the datasets?

`GET /intents/export?format=csv` (or `?format=json`), and the same for
`/wake_words/export` and `/utterances/export`, with a hard cap of 100k rows
per request. See [docs/datasets.md](docs/datasets.md) for column meanings and
notes on building training sets, and
[docs/api-reference.md](docs/api-reference.md) for every filter parameter.

## How are dashboard stats cached?

In-memory, server-side, for `DASHBOARD_CACHE_TTL` seconds (default 60) — see
[docs/dashboard.md](docs/dashboard.md).

## How do I run tests?

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest test/ -v --cov=app --cov-report=term-missing
```

See [docs/development.md](docs/development.md) for the full contributor
guide.
