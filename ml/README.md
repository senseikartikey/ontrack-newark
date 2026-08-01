# /ml

Owned by `ml-engineer-agent`. Computes predicted delay risk for Newark-area rail lines.

## Status
- **v1 statistical baseline** (`compute_baseline.py`): average observed delay per (line, hour-of-day, day-of-week) bucket, written to `delay_baseline`. Verified against both synthetic data and real production data.
- **v2 LightGBM model** (`train_model.py`, `features.py`): built and logic-verified end-to-end against synthetic data — feature engineering, a time-based train/test split, training, and evaluation against the baseline all confirmed correct (synthetic test: model MAE 31.6s vs. baseline MAE 128.3s, correctly identified as a win). **Not yet trained on real data** — run against the real database on 2026-08-01 and correctly reported `skipped_insufficient_data` (47 real rows vs. a 500-row minimum) rather than fitting an overfit model. This is expected: real GTFS-RT ingestion only started 2026-08-01. Re-run automatically every day via GitHub Actions; will start training for real once enough history accumulates.
- **Serving**: the backend's `/predict` prefers a `ml_predictions` row over `delay_baseline` when both exist for a bucket — see `backend/routers/lines.py`. Since `train_model.py` only ever writes a bucket after the model has beaten the baseline on a held-out test set, "a row exists" already implies "it's worth preferring."

## Design notes
- `MIN_TRAINING_ROWS` (`config.py`, currently 500) gates `train_model.py` the same way `MIN_SAMPLES_THRESHOLD` gates the baseline — an explicit, logged skip rather than silently training (and potentially serving) a model fit on too little data. Not tuned against real data yet; revisit once there's real volume to reason about.
- `MIN_SAMPLES_THRESHOLD` (currently 20) gates the v1 baseline the same way.
- Feature set (`features.py`): line, direction, scheduled hour, day-of-week, temperature/wind/precipitation (nearest-hour join to `weather_hourly`), active alert count for the line, and a same-line "recent average delay" feature (mean delay of other same-line trips in the preceding 60 minutes — an "is this line running behind right now" signal, computed with an explicit scan rather than a pandas time-rolling window so it's easy to verify there's no leakage from a row into its own feature).
- Train/test split is **time-based** (last 20% by `scheduled_time`), never random — a trip's repeated GTFS-RT readings are correlated, so a random split would leak information between train and test.
- The v1 baseline deliberately does **not** bucket by weather — a finer bucket means sparser samples, which matters more when data is scarce. The v2 model uses weather as a continuous feature instead, which doesn't have this sparsity problem.
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
python train_model.py
```
Both safe to run repeatedly. In production these run daily via the GitHub Actions workflow in `/.github/workflows/baseline.yml` — the underlying delay distribution shifts slowly, so daily recomputation is plenty.
