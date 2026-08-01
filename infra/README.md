# /infra

Owned by `devops-engineer-agent`. Scheduled ingestion/compute workflows live in `/.github/workflows/` (GitHub Actions requires them at the repo root, not inside `/infra` itself — this file documents them).

## Workflows
- **`ingest.yml`** — every 5 minutes: `poll_weather.py`, `poll_gtfs_rt.py`, `poll_alerts.py`. All three verified working against the real APIs as of 2026-08-01 — see `ENGINEERING_LOG.md`.
- **`static-gtfs.yml`** — weekly: `static_gtfs_loader.py` (the static feed changes rarely).
- **`baseline.yml`** — daily: `compute_baseline.py` (the delay distribution shifts slowly).

## Why 5 minutes, not 60-120s
The project plan describes 60-120s polling as ideal for a dedicated worker. GitHub Actions' cron has no finer granularity than a minute, and scheduled runs aren't guaranteed to fire exactly on time besides. 5 minutes is the practical floor for this free-tier approach.

## Required GitHub repo secrets
Set these under Settings → Secrets and variables → Actions:
- `DATABASE_URL` — the Supabase Postgres connection string (same one used locally).
- `NJT_USERNAME` / `NJT_PASSWORD` — from the NJ Transit developer portal, once registered.
- `WEATHER_USER_AGENT` — a descriptive string per NWS API policy (e.g. `"OnTrackNewark (contact: you@example.com)"`).

## Keep this repo public
GitHub Actions minutes are unlimited for public repos and capped at 2000 min/month for private ones. At a 5-minute ingestion cadence, a private repo would exhaust that quota in days. Since this is a portfolio project anyway, keep it public rather than reducing polling frequency to fit a private-repo budget.

## Deployment (not yet set up)
Per the project plan: Supabase (Postgres), Render/Railway (backend), Vercel (frontend). Not configured yet — this file will get a deploy section once that happens.
