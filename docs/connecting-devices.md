# Connecting an OVOS Device

This page is for people running OVOS on a device — a satellite, a desktop
install, a Raspberry Pi — who want to contribute data to an open-data server,
either the public community instance or one they host themselves.

Everything here is **opt-in and off by default**. Nothing described below
happens unless you add an `open_data` block to your device's `mycroft.conf`.

## Why bother

Wake-word and speech datasets are hard to build and usually locked inside a
single company. Every OVOS device that opts in adds real, diverse samples —
different accents, rooms, and languages — to a dataset the whole community
gets to use. You choose exactly which categories of data you send, and to
which server.

## The `open_data` config block

On the device, edit `mycroft.conf` (or an override file under
`~/.config/mycroft/mycroft.conf`) and add an `open_data` section. Each key is
independent — set only the ones you want.

### Send everything to the public instance

```json
{
  "open_data": {
    "intent_urls": ["https://metrics.tigregotico.pt/intents"],
    "ww_urls": ["https://metrics.tigregotico.pt/wake_word"],
    "stt_urls": ["https://metrics.tigregotico.pt/stt"]
  }
}
```

- `intent_urls` — `ovos-core`'s intent pipeline posts every matched intent
  here.
- `ww_urls` — `ovos-dinkum-listener` posts every wake-word detection here.
- `stt_urls` — `ovos-dinkum-listener` posts every recognized STT utterance
  here.

Each key takes a **list** of URLs — a device can report to more than one
server at once (for example, the public instance and your own).

### Intents only, nothing else

If you're comfortable sharing what you say to your assistant as text, but not
audio recordings, set only `intent_urls`:

```json
{
  "open_data": {
    "intent_urls": ["https://metrics.tigregotico.pt/intents"]
  }
}
```

No wake-word or STT audio ever leaves the device with this configuration.

### Pointing at your own server

Run [self-hosting.md](self-hosting.md) yourself and point the device there
instead:

```json
{
  "open_data": {
    "intent_urls": ["https://metrics.example.com/intents"],
    "ww_urls": ["https://metrics.example.com/wake_word"],
    "stt_urls": ["https://metrics.example.com/stt"]
  }
}
```

Your data, your rules — nothing leaves your own network.

### With an API key

If the server you're reporting to requires an API key (set via `API_KEY` on
the server — see [self-hosting.md](self-hosting.md)), configure it on the
device:

```json
{
  "open_data": {
    "intent_urls": ["https://metrics.example.com/intents"],
    "ww_urls": ["https://metrics.example.com/wake_word"],
    "stt_urls": ["https://metrics.example.com/stt"],
    "api_key": "your-shared-secret",
    "user_agent": "ovos-metrics"
  }
}
```

- `api_key` is sent as the `X-API-Key` header on every upload.
- `user_agent` defaults to `"ovos-metrics"` and normally doesn't need to be
  set — the server rejects any other value. Only change it if your server
  operator asked you to (for example, to segment traffic from a fleet of
  devices).

## What exactly gets uploaded

| Endpoint | What is sent | What is never sent |
|----------|--------------|---------------------|
| `/intents` | Utterance text, matched intent name, language, and (if available) the pipeline stage that matched and the device's `ovos-core` version | Audio, device identifiers, account info |
| `/wake_word` | The WAV recording of the wake-word trigger, wake-word name, model, plugin, language | Anything said *after* the wake word (that's a separate, opt-in STT upload) |
| `/stt` | The WAV recording of the spoken command and its transcript, model, plugin, language | Persistent audio storage tied to your identity — no account or device ID is attached |

No personally identifiable information is collected by design — see
[privacy.md](../privacy.md) for the full policy. Submitted data cannot be
retracted after the fact, because the server has no way to verify who sent
it; if you're not comfortable with that, don't opt in, or point your device
at a server you control and delete records there directly.

## Verifying uploads are arriving

The dashboard (`/` on your server, or
[https://opendata.tigregotico.pt](https://opendata.tigregotico.pt) for the
public instance) shows live counts and lets you filter by language, intent,
or wake word. After triggering your assistant a few times, refresh the
dashboard and look for your samples in the relevant tab.

You can also query the API directly. For example, to see the most recent
intent matches for your language:

```bash
curl "https://metrics.tigregotico.pt/intents?lang=en-us&limit=5"
```

If nothing shows up:

- Double-check the URLs in `open_data` are reachable from the device
  (`curl -I <url>` should not time out).
- Confirm the device actually triggered that pipeline (say a wake word, ask a
  question that resolves to an intent).
- Check the device logs for upload errors — a `401` means a missing or wrong
  `api_key`; a `429` means you're being rate limited by the server.

## Turning it off

Remove the `open_data` block (or the specific URL list you no longer want)
from `mycroft.conf` and restart the affected service. There is no separate
"disable" flag — an empty or missing `open_data` config means no uploads at
all, which is also the default for a fresh install.
