# API Reference

## Intake Endpoints

All intake endpoints require `User-Agent: ovos-metrics` or return `404`.

| Method | Path | Form Fields | Notes |
|--------|------|------------|-------|
| POST | `/intents` | `utterance`, `intent`, `lang`, `match_data?` | Language normalized to lowercase |
| POST | `/wake_word` | `name`, `audio` (file), `model?`, `lang?`, `plugin?`, `plugin_config?` | Audio limited by `MAX_AUDIO_SIZE_MB` (default 10) |
| POST | `/stt` | `transcript`, `lang`, `audio` (file), `model?`, `plugin?`, `plugin_config?` | Audio limited by `MAX_AUDIO_SIZE_MB` |

**Errors**: `413` if audio exceeds limit; `404` for wrong User-Agent.

---

## Query Endpoints

### GET `/intents`
Returns `PaginatedResponse[IntentRecord]`.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lang` | str | — | Filter by language (case-insensitive) |
| `intent` | str | — | Exact intent name filter |
| `date_from` | datetime | — | ISO 8601 lower bound |
| `date_to` | datetime | — | ISO 8601 upper bound |
| `page` | int | 1 | 1-based page number |
| `limit` | int | 50 | Max 500 |

### GET `/wake_words`
Returns `PaginatedResponse[WakeWordRecord]`.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | — | Wake-word name filter |
| `model` | str | — | Model identifier filter |
| `plugin` | str | — | Plugin name filter |
| `lang` | str | — | Language filter |
| `page` | int | 1 | |
| `limit` | int | 50 | Max 500 |

### GET `/utterances`
Returns `PaginatedResponse[UtteranceRecord]`.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lang` | str | — | Language filter |
| `model` | str | — | Model name filter |
| `plugin` | str | — | Plugin name filter |
| `page` | int | 1 | |
| `limit` | int | 50 | Max 500 |

---

## Audio Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/wake_words/{id}/audio` | `audio/wav` stream; `404` if not found |
| GET | `/utterances/{id}/audio` | `audio/wav` stream; `404` if not found |

---

## Export Endpoints

All accept `format=csv` (default) or `format=json`. Hard cap: 100k rows. Accept the same filters as the corresponding query endpoint.

| Path | Extra filters |
|------|--------------|
| `GET /intents/export` | `lang`, `intent`, `date_from`, `date_to` |
| `GET /wake_words/export` | `name`, `model`, `plugin`, `lang` |
| `GET /utterances/export` | `lang`, `model`, `plugin` |

---

## Dashboard Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/dashboard/stats` | `DashboardStats` JSON (60s TTL cache) |
| GET | `/` | HTML dashboard page |
| GET | `/status` | `{"status": "success"}` |

### DashboardStats schema

```json
{
  "total_intents": 0,
  "total_wake_words": 0,
  "total_utterances": 0,
  "intent_distribution": {"IntentName": 42},
  "language_distribution": {"en-us": 100},
  "wake_word_distribution": {"hey mycroft": 55}
}
```

### PaginatedResponse schema

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```
