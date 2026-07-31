# /ingestion

Owned by `data-engineer-agent`. Collects NJ Transit rail delay data and Newark-area weather into Postgres.

## Status
- **Weather (`weather_client.py`, `poll_weather.py`)**: working, verified live against `api.weather.gov`. No API key needed.
- **Static GTFS (`static_gtfs_loader.py`)**: working, verified live against NJ Transit's public `rail_data.zip` (no auth required). Loads `routes`/`stops` reference tables. Also used to verify the real `NEWARK_AREA_LINES` codes and Newark station stop_ids in `config.py` — see `ENGINEERING_LOG.md` (2026-07-30).
- **NJ Transit RailData / GTFS-RT (`njt_client.py`, `poll_gtfs_rt.py`)**: scaffolded but **blocked on real credentials**. Unlike the static feed, this one requires developer portal registration and its docs are only visible after logging in. Every `TODO` in `njt_client.py` and `poll_gtfs_rt.py` needs to be checked against the real API reference once you have access, before this will actually pull live delay data.

## Setup
```
python -m venv .venv
.venv/Scripts/activate      # .venv/bin/activate on Mac/Linux
pip install -r requirements.txt
cp .env.example .env         # then fill in DATABASE_URL, NJT_USERNAME, NJT_PASSWORD
```

## What you (Kartikey) need to do manually
1. **NJ Transit developer account**: register at https://developer.njtransit.com/registration/, agree to terms, and request access to the **RailData API**. Put the resulting username/password in `.env` as `NJT_USERNAME`/`NJT_PASSWORD`.
2. Once you can see the RailData API reference in the portal, open `njt_client.py` and `poll_gtfs_rt.py` and resolve each `TODO` — confirm the real token endpoint, the vehicle-data endpoint, and the actual JSON field names, then update the placeholders.
3. **Supabase project**: create a free project at https://supabase.com, grab the Postgres connection string (Project Settings → Database → Connection string → URI), and put it in `.env` as `DATABASE_URL`.

## Running locally
```
python poll_weather.py     # works today
python poll_gtfs_rt.py     # will work once step 1-2 above are done
```

## Scheduling
In production these run on a schedule via a GitHub Actions workflow (owned by `devops-engineer-agent`, in `/infra`), not a long-lived worker — see `AGENTS.md` for why (free-tier worker sleep limits).
