# /ingestion

Owned by `data-engineer-agent`. Collects NJ Transit rail delay data and Newark-area weather into Postgres.

## Status — everything is live
- **Weather (`weather_client.py`, `poll_weather.py`)**: working, verified live against `api.weather.gov`. No API key needed.
- **Static GTFS (`static_gtfs_loader.py`)**: working, verified live against NJ Transit's public `rail_data.zip` (no auth required). Loads `routes`/`stops` reference tables.
- **NJ Transit RailData / GTFS-RT (`njt_client.py`, `poll_gtfs_rt.py`)**: working, verified live 2026-08-01 against the real API (RailData access approved). Real train delay data is flowing into `trip_updates` for all 6 distinct Newark-area lines (NEC, NJCL, RARV, BNTN, MNE, MNEG). See `njt_client.py`'s docstring for the confirmed request/response shapes, and `config.py`'s `TRAIN_LINE_TO_CODE` for how the live feed's full line names (e.g. `"Northeast Corridor Line"`) map to our route codes.

## Setup
```
python -m venv .venv
.venv/Scripts/activate      # .venv/bin/activate on Mac/Linux
pip install -r requirements.txt
cp .env.example .env         # then fill in DATABASE_URL, NJT_USERNAME, NJT_PASSWORD
```

Note (Windows): `zoneinfo` needs the `tzdata` package on Windows since it doesn't ship IANA timezone data — already in `requirements.txt`. Linux (including GitHub Actions runners) usually has system tzdata already, but the package is harmless there too.

## Running locally
```
python poll_weather.py
python static_gtfs_loader.py
python poll_gtfs_rt.py
```
All three work end-to-end today.

## Known limitation
`NEXT_STOP` in the live vehicle-data feed is a human-readable station name (e.g. `"Ridgewood"`), not the numeric `stop_id` static GTFS uses (e.g. `"107"`) — the two ID systems don't share a key, and there's no name-matching layer built yet. We store the station name as-is in the `stop_id` column; it's more immediately readable than an opaque ID would be, but it means `trip_updates.stop_id` isn't currently joinable against `stops.stop_id`. Worth revisiting if a feature needs that join (e.g. a map view).

## Scheduling
In production these run on a schedule via GitHub Actions workflows (owned by `devops-engineer-agent`, in `/.github/workflows/`, documented in `/infra/README.md`), not a long-lived worker — see `AGENTS.md` for why (free-tier worker sleep limits).
