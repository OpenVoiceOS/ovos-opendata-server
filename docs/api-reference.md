# API Reference

Base URL for the public instance: `https://metrics.openvoiceos.pt`. For a
self-hosted instance, substitute your own host.

## Intake Endpoints

All intake endpoints require `User-Agent: ovos-metrics` — any other value
returns `404` (intentionally, to avoid making the write API discoverable to
casual scanners). If the server has `API_KEY` configured, requests must also
send a matching `X-API-Key` header. Wake-word and STT uploads are validated
as real WAV files before being stored. All three endpoints are rate limited
per client IP (`RATE_LIMIT`, default `60/minute`).

| Method | Path | Form Fields | Notes |
|--------|------|------------|-------|
| POST | `/intents` | `utterance`, `intent`, `lang`, `match_data?`, `pipeline?`, `core_version?` | `lang` is normalized to lowercase; `pipeline` is a pipe-joined list of pipeline stages attempted before this intent matched (e.g. `adapt_high\|padatious_high`); `core_version` is the reporting device's `ovos-core` version |
| POST | `/wake_word` | `name`, `audio` (file), `model?`, `lang?`, `plugin?`, `plugin_config?` | `audio` limited by `MAX_AUDIO_SIZE_MB` (default 10) and must be a valid WAV file |
| POST | `/stt` | `transcript`, `lang`, `audio` (file), `model?`, `plugin?`, `plugin_config?` | `audio` limited by `MAX_AUDIO_SIZE_MB` and must be a valid WAV file |

**Errors**

| Code | Meaning |
|------|---------|
| `400` | Uploaded audio is not a valid WAV file |
| `401` | `API_KEY` is configured on the server and the request's `X-API-Key` header is missing or wrong |
| `404` | Wrong or missing `User-Agent` header |
| `413` | Audio exceeds `MAX_AUDIO_SIZE_MB` |
| `429` | Caller exceeded `RATE_LIMIT` |

**Examples**

```bash
curl -X POST https://metrics.openvoiceos.pt/intents \
  -H "User-Agent: ovos-metrics" \
  -F utterance="what time is it" \
  -F intent="query_time" \
  -F lang="en-us" \
  -F pipeline="adapt_high" \
  -F core_version="0.0.8"
```

```bash
curl -X POST https://metrics.openvoiceos.pt/wake_word \
  -H "User-Agent: ovos-metrics" \
  -F name="hey mycroft" \
  -F lang="en-us" \
  -F model="hey_mycroft.tflite" \
  -F plugin="ovos-ww-plugin-precise-lite" \
  -F audio=@wakeword.wav
```

```bash
curl -X POST https://metrics.openvoiceos.pt/stt \
  -H "User-Agent: ovos-metrics" \
  -F transcript="turn on the lights" \
  -F lang="en-us" \
  -F model="whisper-base" \
  -F plugin="ovos-stt-plugin-server" \
  -F audio=@utterance.wav
```

With an `X-API-Key` header (only needed if the server configures `API_KEY`):

```bash
curl -X POST https://metrics.example.com/intents \
  -H "User-Agent: ovos-metrics" \
  -H "X-API-Key: your-shared-secret" \
  -F utterance="what time is it" \
  -F intent="query_time" \
  -F lang="en-us"
```

---

## Query Endpoints

Read endpoints have no auth requirement — they're meant to be public. All
support pagination via `page` (1-based, default `1`) and `limit` (default
`50`, max `500`); results are ordered newest first.

### GET `/intents`

Returns `PaginatedResponse[IntentRecord]`.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lang` | str | — | Filter by language (case-insensitive) |
| `intent` | str | — | Exact intent name filter |
| `date_from` | datetime | — | ISO 8601 lower bound (inclusive) |
| `date_to` | datetime | — | ISO 8601 upper bound (inclusive) |
| `page` | int | 1 | 1-based page number |
| `limit` | int | 50 | Max 500 |

```bash
curl "https://metrics.openvoiceos.pt/intents?lang=en-us&page=1&limit=20"
```

### GET `/wake_words`

Returns `PaginatedResponse[WakeWordRecord]` (audio bytes excluded — use the
audio endpoint below to fetch a specific recording).

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | — | Wake-word name filter |
| `model` | str | — | Model identifier filter |
| `plugin` | str | — | Plugin name filter |
| `lang` | str | — | Language filter (case-insensitive) |
| `page` | int | 1 | |
| `limit` | int | 50 | Max 500 |

```bash
curl "https://metrics.openvoiceos.pt/wake_words?name=hey+mycroft&limit=10"
```

### GET `/utterances`

Returns `PaginatedResponse[UtteranceRecord]` (audio bytes excluded).

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lang` | str | — | Language filter |
| `model` | str | — | Model name filter |
| `plugin` | str | — | Plugin name filter |
| `page` | int | 1 | |
| `limit` | int | 50 | Max 500 |

```bash
curl "https://metrics.openvoiceos.pt/utterances?lang=pt-pt"
```

---

## Audio Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/wake_words/{id}/audio` | `audio/wav` stream; `404` if no record with that id exists |
| GET | `/utterances/{id}/audio` | `audio/wav` stream; `404` if no record with that id exists |

```bash
curl -o sample.wav "https://metrics.openvoiceos.pt/wake_words/42/audio"
```

---

## Export Endpoints

All accept `format=csv` (default) or `format=json` and accept the same
filters as the corresponding query endpoint. Exports are capped at 100,000
rows per request; page through by narrowing the filters (e.g. by
`date_from`/`date_to`) if you need more.

| Path | Extra filters |
|------|--------------|
| `GET /intents/export` | `lang`, `intent`, `date_from`, `date_to` |
| `GET /wake_words/export` | `name`, `model`, `plugin`, `lang` |
| `GET /utterances/export` | `lang`, `model`, `plugin` |

```bash
curl -o intents.csv "https://metrics.openvoiceos.pt/intents/export?format=csv&lang=en-us"
curl -o wake_words.json "https://metrics.openvoiceos.pt/wake_words/export?format=json"
```

Invalid `format` values return `400`.

---

## Dashboard Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/dashboard/stats` | `DashboardStats` JSON, cached server-side for `DASHBOARD_CACHE_TTL` seconds (default 60) |
| GET | `/` | HTML dashboard page |
| GET | `/status` | `{"status": "success"}` — health check |

### `DashboardStats` schema

```json
{
  "total_intents": 15234,
  "total_wake_words": 4021,
  "total_utterances": 3890,
  "intent_distribution": {"query_time": 42, "light_on": 30},
  "language_distribution": {"en-us": 12000, "pt-pt": 900},
  "wake_word_distribution": {"hey mycroft": 3500}
}
```

### `PaginatedResponse` schema

```json
{
  "items": [ /* IntentRecord | WakeWordRecord | UtteranceRecord */ ],
  "total": 15234,
  "page": 1,
  "limit": 50,
  "pages": 305
}
```

`IntentRecord` fields: `id`, `intent`, `language`, `utterance`, `pipeline`
(nullable), `core_version` (nullable), `created_at`.

`WakeWordRecord` fields: `id`, `wake_word` (nullable), `model` (nullable),
`plugin` (nullable), `language` (nullable), `created_at`. No audio.

`UtteranceRecord` fields: `id`, `model` (nullable), `plugin` (nullable),
`language` (nullable), `created_at`. No transcript or audio in the list view
— fetch a single record's audio via `/utterances/{id}/audio`, or use the
export endpoint for the transcript text.

See also: [datasets.md](datasets.md) for what these columns mean in practice
and how to build a training set from them.
