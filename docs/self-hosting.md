# Self-Hosting

This is the operator's guide: running ovos-opendata-server in production, for
your own devices or a community. If you just want to try it locally first,
see [getting-started.md](getting-started.md).

## Architecture at a glance

```
OVOS device(s)
   │  POST /intents, /wake_word, /stt   (User-Agent: ovos-metrics, optional X-API-Key)
   ▼
FastAPI app (uvicorn)
   ├─ app/routers/data_intake.py   — validates and stores uploads
   ├─ app/routers/query.py        — paginated read API
   ├─ app/routers/audio.py        — streams individual WAV files
   ├─ app/routers/export.py       — bulk CSV/JSON export
   └─ app/routers/dashboard.py    — cached stats + HTML dashboard
   │
   ▼
PostgreSQL (or SQLite for local/dev)
```

The app is stateless aside from the database — you can run multiple API
containers behind a load balancer pointed at the same Postgres instance if
you need to scale.

## Production Docker Compose setup

The shipped `docker-compose.yml` runs the API and a Postgres 16 container
side by side:

```yaml
name: ovos-opendata
services:
  ovos-opendata-api:
    build: .
    container_name: ovos-opendata-api
    image: ovos-opendata/api
    restart: unless-stopped
    ports:
      - "8007:8000"
    env_file: .env
    depends_on:
      - ovos-opendata-db

  ovos-opendata-db:
    image: postgres:16
    container_name: ovos-opendata-db
    restart: unless-stopped
    env_file: .env
    volumes:
      - ~/.local/share/ovos-opendata:/var/lib/postgresql/data
```

1. Copy `.env.example` to `.env` and fill in real credentials:

   ```bash
   cp .env.example .env
   ```

   ```
   DATABASE_URL=postgresql://ovos:CHANGE_ME@ovos-opendata-db:5432/ovos_metrics
   POSTGRES_USER=ovos
   POSTGRES_PASSWORD=CHANGE_ME
   POSTGRES_DB=ovos_metrics
   MAX_AUDIO_SIZE_MB=10
   ```

   Note `DATABASE_URL` uses the Compose service name (`ovos-opendata-db`) as
   the host, not `localhost` — the two containers talk over the Compose
   network.

2. Bring it up:

   ```bash
   docker compose up --build -d
   ```

   The container entrypoint (`scripts/entrypoint.sh`) runs
   `alembic upgrade head` before starting `uvicorn`, so the schema is always
   current on boot — you never need to run migrations by hand in this setup.

3. Postgres data persists in `~/.local/share/ovos-opendata` on the host.
   Change that volume path in `docker-compose.yml` if you want the data
   somewhere else (for example, a separate disk).

Prefer a prebuilt image over building locally? Tagged releases are published
to `ghcr.io/openvoiceos/ovos-opendata-server`; swap `build: .` for
`image: ghcr.io/openvoiceos/ovos-opendata-server:latest` (or a pinned version
tag) in the compose file.

## Environment variable reference

| Variable | Required | Default | What it controls |
|----------|----------|---------|-------------------|
| `DATABASE_URL` | No | `sqlite:///./ovos_opendata.db` | Database DSN. The SQLite default is fine for trying things out; **always set a PostgreSQL DSN in production** — SQLite doesn't handle concurrent writers well and audio blobs bloat a single file fast. |
| `MAX_AUDIO_SIZE_MB` | No | `10` | Hard cap, in MB, on any single wake-word or STT audio upload. Oversized uploads get `413`. Raise this if your STT plugin sends longer utterances; keep it as low as your traffic tolerates to bound storage growth and abuse. |
| `API_KEY` | No | unset | When set, `/intents`, `/wake_word`, and `/stt` also require a matching `X-API-Key` header, in addition to the `User-Agent` check. Leave unset for a fully public intake endpoint (like the community instance); set it to restrict uploads to devices you've configured. |
| `RATE_LIMIT` | No | `60/minute` | Per-client-IP rate limit on the three intake endpoints, in [slowapi](https://github.com/laurentS/slowapi) limit-string syntax (e.g. `"10/minute"`, `"1000/hour"`). Exceeding it returns `429`. |
| `DASHBOARD_CACHE_TTL` | No | `60` | Seconds the `/dashboard/stats` aggregation query result is cached in memory. Raise it on a busy instance to cut database load; lower it if you want the dashboard to feel closer to real time. |

Settings are loaded from the environment and, if present, from a `.env` file
in the working directory (`app/config.py`, via `pydantic-settings`). The read
API and dashboard have no auth — they're meant to be public — so put them
behind your reverse proxy's own access controls if that's not what you want.

## The trust model

Every layer here defends against a different problem:

- **User-Agent gate** (`User-Agent: ovos-metrics`, always on) — stops casual
  browsers and generic scanners from discovering the write endpoints. It
  intentionally returns `404`, not `403`, so a bot probing the API can't even
  tell the endpoint exists.
- **API key** (`X-API-Key`, optional via `API_KEY`) — the real access
  control. Off by default so a public community instance stays open; turn it
  on if you're running a private or fleet-restricted server and want to
  reject devices you haven't explicitly configured.
- **Rate limiting** (`RATE_LIMIT`, per client IP) — bounds how much any one
  source can write, so a misbehaving or malicious device can't flood the
  database or fill your disk.
- **Audio validation** — uploaded wake-word and STT audio must be a real WAV
  file (checked by its RIFF/WAVE header) before it's stored; malformed
  uploads are rejected with `400` rather than silently corrupting the
  dataset.
- **Size caps** (`MAX_AUDIO_SIZE_MB`) — bounds how much storage a single
  upload can consume, independent of how many uploads there are.

None of this replaces network-level protections — put a reverse proxy in
front for TLS and, if you want, additional IP allow-listing.

## Reverse proxy + TLS

Terminate TLS in front of uvicorn rather than in the app itself. Two common
options:

**Caddy** (automatic HTTPS via Let's Encrypt, minimal config):

```
metrics.example.com {
    reverse_proxy localhost:8007
}
```

**nginx**:

```nginx
server {
    listen 443 ssl;
    server_name metrics.example.com;

    ssl_certificate     /etc/letsencrypt/live/metrics.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/metrics.example.com/privkey.pem;

    client_max_body_size 20m;  # comfortably above MAX_AUDIO_SIZE_MB

    location / {
        proxy_pass http://127.0.0.1:8007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Set `client_max_body_size` (nginx) or your proxy's equivalent above
`MAX_AUDIO_SIZE_MB`, or large-but-valid uploads will be rejected by the proxy
before the app ever sees them.

## Backups

Everything that matters lives in Postgres — audio is stored as blobs in the
database, not on disk separately, so a database backup is a full backup.

```bash
# dump
docker exec ovos-opendata-db pg_dump -U ovos ovos_metrics | gzip > backup-$(date +%F).sql.gz

# restore into a fresh database
gunzip -c backup-2026-01-01.sql.gz | docker exec -i ovos-opendata-db psql -U ovos ovos_metrics
```

Schedule the dump on a cron job and ship it somewhere off the host. Because
audio blobs make the database grow quickly, keep an eye on disk usage and
consider periodically exporting and pruning very old records if storage is a
concern for your instance — there's no built-in retention/expiry policy, so
this is a manual, operator-side decision.

## Upgrading

```bash
git pull
docker compose up --build -d
```

The entrypoint runs `alembic upgrade head` automatically on every container
start, so schema migrations apply themselves — you don't need a separate
migration step. Read the release notes for anything that isn't a pure
additive schema change before upgrading a production instance, and take a
backup first regardless.
