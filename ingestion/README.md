# /ingestion

Owned by `data-engineer-agent`. Collects NJ Transit rail delay data and Newark-area weather into Postgres.

## Status — everything is live
- **Weather (`weather_client.py`, `poll_weather.py`)**: working, verified live against `api.weather.gov`. No API key needed.
- **Static GTFS (`static_gtfs_loader.py`)**: working, verified live against NJ Transit's public `rail_data.zip` (no auth required). Loads `routes`/`stops`/`trips`/`stop_times` reference tables -- `trips`/`stop_times` give each trip's ordered stop sequence (needed for the "on this train" companion view and the Newark-hub transfer view, see `docs/PRD-v2.md`). `stop_times` is ~46k rows on the real feed, upserted in batches of 1000 rows per `session.execute()` call (row-at-a-time was impractically slow against the remote Supabase connection at that volume; routes/stops/trips stay row-at-a-time since they're small).
- **NJ Transit RailData / GTFS-RT (`njt_client.py`, `poll_gtfs_rt.py`)**: working, verified live 2026-08-01 against the real API (RailData access approved). Real train delay data is flowing into `trip_updates` for all 6 distinct Newark-area lines (NEC, NJCL, RARV, BNTN, MNE, MNEG). See `njt_client.py`'s docstring for the confirmed request/response shapes, and `config.py`'s `TRAIN_LINE_TO_CODE` for how the live feed's full line names (e.g. `"Northeast Corridor Line"`) map to our route codes.
- **Service alerts (`poll_alerts.py`)**: working, verified live 2026-08-01 against the real `getStationMSG` endpoint. Real alerts (cancellations, delays) flow into `service_alerts`, filtered to Newark-area lines via `config.match_line_scope` (handles the feed's inconsistent `MSG_LINE_SCOPE` casing/formatting, e.g. `"*MontClair-Boonton Line"`).
- **Feed anomaly reconciliation (`reconcile_anomalies.py`)**: runs inside every `poll_gtfs_rt.py` invocation (before that poll's own `trip_updates` insert) and writes to a new additive `feed_anomalies` table. Detects two known NJ Transit live-feed unreliability patterns (see `docs/PRD-v2.md`'s data-confidence-indicator research): `vanished_mid_route` (a trip whose own next-stop ETA hadn't passed yet simply disappears from the feed on the next poll, with no plausible explanation like route completion) and `stale_timestamp` (a trip's `scheduled_time`/`actual_time`/`delay_seconds` stay byte-identical across 3+ consecutive polls despite `collected_at` advancing, suggesting a cached rather than fresh reading). See the module docstring for the full detection logic and its one known limitation (no ground truth for a trip's actual terminus, since GTFS-RT's `NEXT_STOP` and static GTFS's `trip_id` don't share a key -- see the "Known limitation" section below). Verified against real production `trip_updates` history (a genuine `vanished_mid_route` case was caught retrospectively) plus synthetic edge cases for `stale_timestamp` and the negative "normal completion" case -- see `ENGINEERING_LOG.md` for exactly what was verified against real vs. synthetic data.
- **Track assignments (`poll_track_assignments.py`)**: code-complete and DB-verified (real payload replay + real Postgres writes -- see ENGINEERING_LOG.md's 2026-08-02 entry), but **not yet run live end-to-end** -- deferred until NJT's account-wide daily `getToken` quota (discovered this session, see below) resets. Logs a time series of scheduled track assignments (`track_assignments` table) for a curated set of Newark-area multi-track/junction stations (see `TRACK_ASSIGNMENT_STATIONS` in `config.py`), using NJT RailData's `getTrainSchedule` endpoint and yet another distinct station-identifier space (NJT's own 2-character station codes, e.g. `"NP"`) -- see the module docstring and models.py's `TrackAssignment` docstring. Deliberately always includes `"NY"` (New York Penn Station) even though its `TRACK` is expected to come back empty on essentially every reading (Amtrak-dispatched, no NJT early visibility) -- that is a real, honest finding worth logging over time, not a bug. **Not yet wired into `/.github/workflows/ingest.yml`** -- needs a `devops-engineer-agent` change to add it on the same 5-minute cadence as the other three scripts.
- **NJT RailData daily quota (all NJT-authenticated scripts above)**: NJT enforces a low account-wide daily quota on `getToken` issuance -- discovered live 2026-08-02 via a real `{"errorMessage":"Daily usage limit:10. Your current daily usage: 11"}` response. `njt_client.py` now persists issued tokens to a new `njt_token_cache` table (on by default) so every poller process shares one token across the ~25-minute assumed TTL instead of each 5-minute scheduled invocation minting its own -- see ENGINEERING_LOG.md for the full root-cause writeup and what's still unverified (a fresh live token fetch succeeding end-to-end, blocked today by the exhausted quota).

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
python poll_alerts.py
python poll_track_assignments.py
```
The first four work end-to-end today. `poll_track_assignments.py` is code-complete and DB-verified but not yet confirmed against a real live `getTrainSchedule` call end-to-end -- see "Status" above.

## Known limitation
`NEXT_STOP` in the live vehicle-data feed is a human-readable station name (e.g. `"Ridgewood"`), not the numeric `stop_id` static GTFS uses (e.g. `"107"`) — the two ID systems don't share a key, and there's no name-matching layer built yet. We store the station name as-is in the `stop_id` column; it's more immediately readable than an opaque ID would be, but it means `trip_updates.stop_id` isn't currently joinable against `stops.stop_id`. Worth revisiting if a feature needs that join (e.g. a map view).

## Scheduling
In production these run on a schedule via GitHub Actions workflows (owned by `devops-engineer-agent`, in `/.github/workflows/`, documented in `/infra/README.md`), not a long-lived worker — see `AGENTS.md` for why (free-tier worker sleep limits).
