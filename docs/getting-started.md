# Getting Started

This page is for total beginners: you've never touched this project before
and want to see it running with real-looking data in a few minutes.

## What this server is

OVOS voice devices can, if you let them, upload small samples of what they
heard: the wake word audio, the STT transcript audio, and the text of
recognized intents. This server is where those uploads go. It stores them in
a database, lets anyone browse aggregate statistics on a dashboard, and lets
anyone export the raw data as CSV or JSON.

## What data it collects, and why

Three kinds of records, each opted into separately on the device:

- **Intents** — the utterance text, which intent it matched, the language,
  and (if the device reports it) which pipeline stage matched and which
  `ovos-core` version sent it. No audio.
- **Wake words** — the WAV recording of the wake-word trigger, plus the wake
  word name, model, plugin, and language.
- **STT utterances** — the WAV recording of a spoken command, plus the
  transcript, model, plugin, and language.

The point is to build open, permissively licensed voice datasets — wake-word
and speech corpora are expensive to collect and usually locked up by
commercial voice assistants. A community-run, opt-in pipeline is the
alternative. See [privacy.md](../privacy.md) for the full policy and
[connecting-devices.md](connecting-devices.md) for exactly what leaves a
device versus what stays local.

## Run it locally

You need Docker and Docker Compose. From the repository root:

```bash
cp .env.example .env
docker compose up --build -d
```

This builds the API image, starts a Postgres container, and runs any pending
database migrations automatically (the container's entrypoint runs
`alembic upgrade head` before starting the server). Give it a few seconds on
first boot, then check it's alive:

```bash
curl http://localhost:8007/status
# {"status":"success"}
```

The API is at `http://localhost:8007` and the dashboard at
`http://localhost:8007/`.

## Seed some demo data

The database starts empty, which makes for a boring dashboard. The `scripts/`
directory has small helper scripts that generate or import sample data.

Random intent matches (no extra dependencies beyond `requests`):

```bash
pip install requests
python scripts/populate_db.py
```

This posts 50 random intent matches to `http://localhost:8000/intents` — note
the script targets port `8000`, the port the API listens on *inside* the
container/network. If you're running the server via `docker compose`
(mapped to host port `8007`), either run the script from inside the
container's network or edit `API_URL` at the top of the script to point at
`http://localhost:8007/intents`.

Real wake-word and STT samples from public Hugging Face datasets (needs
`datasets`, `soundfile`, and `librosa`):

```bash
pip install requests datasets soundfile librosa
python scripts/populate_ww.py    # wake-word samples
python scripts/populate_utt.py   # STT samples
```

These download audio from Hugging Face and upload it exactly the way an OVOS
device would, so they're also a good reference for writing your own client.

## Open the dashboard

Visit `http://localhost:8007/` in a browser. You'll see summary cards for
total intents, wake words, and utterances, plus tabs to browse, filter, and
export each dataset, and a play button to listen to individual audio samples.
See [dashboard.md](dashboard.md) for a full tour.

## Make your first API call

List the most recent intent matches:

```bash
curl "http://localhost:8007/intents?limit=5"
```

Export all wake-word records as CSV:

```bash
curl -o wake_words.csv "http://localhost:8007/wake_words/export?format=csv"
```

Submit an intent match the way a device would (note the required
`User-Agent` header — anything else gets a `404`):

```bash
curl -X POST http://localhost:8007/intents \
  -H "User-Agent: ovos-metrics" \
  -F utterance="what time is it" \
  -F intent="query_time" \
  -F lang="en-us"
```

From here:

- Running your own OVOS device against this server →
  [connecting-devices.md](connecting-devices.md)
- Every endpoint, parameter, and error code →
  [api-reference.md](api-reference.md)
- Taking this to production → [self-hosting.md](self-hosting.md)
