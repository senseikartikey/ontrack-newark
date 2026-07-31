# /ml

Owned by `ml-engineer-agent`. Computes predicted delay risk for Newark-area rail lines.

## Status
- **v1 statistical baseline** (`compute_baseline.py`): average observed delay per (line, hour-of-day, day-of-week) bucket, written to the `delay_baseline` table. Logic verified against synthetic seed data (trip-level dedup, weekday bucketing, and the minimum-sample threshold all behave correctly — see `ENGINEERING_LOG.md`). **Not yet run against real data**, because `/ingestion`'s GTFS-RT poller is still blocked on NJ Transit developer credentials (see `/ingestion/README.md`) — there are zero real `trip_updates` rows to compute from yet.
- **v2 LightGBM model**: not started. Per the project plan, this should only be trained once there are 2-3+ weeks of real ingested data — training on too little data produces a model that looks worse than the baseline, which defeats the point.

## Design notes
- `MIN_SAMPLES_THRESHOLD` (in `config.py`, currently 20) is a starting guess, not tuned against real data — there isn't any yet. Revisit once real volume exists.
- The v1 baseline deliberately does **not** bucket by weather yet, even though the original plan mentioned it — a finer bucket means sparser samples, which matters more when data is scarce. Weather buckets are a reasonable fast-follow once the coarser buckets are reliably clearing the sample threshold.
- Bucketing uses Python's `datetime.weekday()` convention (Monday=0..Sunday=6) throughout — both here and in the backend's `/predict` endpoint — deliberately avoiding Postgres's `EXTRACT(DOW)` (which is Sunday=0) to keep the write side and read side trivially consistent.

## Setup
```
python -m venv .venv
.venv/Scripts/activate      # .venv/bin/activate on Mac/Linux
pip install -r requirements.txt
cp .env.example .env         # same DATABASE_URL as /ingestion and /backend
```

## Running
```
python compute_baseline.py
```
Safe to run repeatedly (upserts). In production this runs on a schedule (daily) via the GitHub Actions workflow in `/infra` — the underlying delay distribution shifts slowly, so daily recomputation is plenty.
