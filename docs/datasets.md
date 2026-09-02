# Using the Data

This page is for people who want to *use* what's been collected — researchers,
model trainers, hobbyists building a wake-word detector — rather than run a
server or contribute from a device.

## Pulling exports

The simplest way to get data out is the export endpoints, which stream CSV or
JSON directly, filtered however you like. See
[api-reference.md](api-reference.md#export-endpoints) for the full parameter
list; a few common pulls:

```bash
# every English intent match, as CSV
curl -o intents_en.csv \
  "https://metrics.tigregotico.pt/intents/export?format=csv&lang=en-us"

# every wake-word record for a specific wake word, as JSON
curl -o hey_mycroft.json \
  "https://metrics.tigregotico.pt/wake_words/export?format=json&name=hey+mycroft"

# intents in a date range
curl -o intents_january.csv \
  "https://metrics.tigregotico.pt/intents/export?format=csv&date_from=2026-01-01T00:00:00&date_to=2026-01-31T23:59:59"
```

Exports cap at 100,000 rows per request. If you need more, split the pull by
date range (`date_from`/`date_to`) or another filter and combine the results
client-side — there's no server-side cursor beyond that cap.

For quick browsing rather than a bulk pull, use the paginated read endpoints
(`GET /intents`, `/wake_words`, `/utterances`) instead — see
[api-reference.md](api-reference.md#query-endpoints).

## Streaming audio by id

Exports and the paginated list endpoints never include raw audio bytes — only
metadata. To fetch the actual WAV for a wake-word or STT record, grab its `id`
from a list/export and request it individually:

```bash
curl -o sample.wav "https://metrics.tigregotico.pt/wake_words/42/audio"
curl -o utterance.wav "https://metrics.tigregotico.pt/utterances/17/audio"
```

A batch download loop is straightforward:

```bash
#!/usr/bin/env bash
# download every wake-word audio file matching a name filter
curl -s "https://metrics.tigregotico.pt/wake_words/export?format=json&name=hey+mycroft" \
  | jq -r '.[].id' \
  | while read -r id; do
      curl -s -o "wake_words/${id}.wav" "https://metrics.tigregotico.pt/wake_words/${id}/audio"
    done
```

## What the columns mean

**Intents** (`/intents/export`): `id`, `intent`, `language`, `utterance`,
`pipeline`, `core_version`, `timestamp`.

- `intent` — the matched intent's registered name.
- `language` — BCP-47 tag, always lowercase (the server normalizes it on
  write regardless of how the device sent it).
- `utterance` — the raw text the user said, as transcribed by the device.
- `pipeline` — a pipe-joined list of pipeline stages `ovos-core` attempted
  before this intent matched, e.g. `adapt_high|padatious_high`. Useful for
  understanding which intent engine actually resolved a given utterance, or
  for studying how deep into the pipeline matches typically happen. May be
  empty if the reporting device didn't send it.
- `core_version` — the `ovos-core` version string of the device that sent
  this record. Useful for filtering out data from very old or unsupported
  versions, or for tracking how behavior changes across `ovos-core` releases.
  May be empty on older devices.

**Wake words** (`/wake_words/export`): `id`, `name`, `model`, `plugin`,
`language`, `timestamp`, plus the audio (fetched separately by `id`).

- `name` — the wake word phrase, e.g. `"hey mycroft"`.
- `model` — the model file/identifier the device used to detect it.
- `plugin` — which wake-word engine plugin was running (e.g.
  `ovos-ww-plugin-precise-lite`).

**Utterances** (`/utterances/export`): `id`, `transcript`, `model`, `plugin`,
`language`, `timestamp`, plus the audio.

- `transcript` — the STT engine's output text for the recording.
- `model` / `plugin` — which STT model and plugin produced the transcript.

## Building training sets

**Wake-word detectors** want (audio, label) pairs. Pull `/wake_words/export`
filtered by `name`, download each `id`'s audio, and pair it with the `name`
field as the label. Use `model`/`plugin` to separate or weight samples by
which detector originally triggered them, since detection quality varies by
plugin.

**STT models** want (audio, transcript) pairs, typically per language. Pull
`/utterances/export` filtered by `lang`, download each `id`'s audio, and pair
it with `transcript`. Because transcripts come from the device's own STT
engine rather than a human, they're noisier than curated speech corpora —
treat them as a large, weakly-labeled dataset rather than gold-standard
transcriptions, and consider a manual or automated review pass before
training on them directly.

**Intent classifiers / NLU** can use `/intents/export` as (utterance, intent,
language) triples directly. `pipeline` and `core_version` are useful for
filtering out low-confidence engines or deprecated pipeline stages before
training.

Because every OVOS device that opts in contributes independently, expect
uneven language and accent coverage — check `language_distribution` on
[`/dashboard/stats`](api-reference.md#dashboard-endpoints) before committing
to a language for a training run.

## Licensing and ethics

Data is collected only from devices whose owners explicitly opted in, and
never includes personally identifiable information by design. It may be
republished as open datasets for community research. Read
[privacy.md](../privacy.md) for the complete policy, including what is and
isn't collected and why submitted records can't be individually deleted on
request.
