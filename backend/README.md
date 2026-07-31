# /backend

Owned by `backend-engineer-agent`. FastAPI app serving live status, predictions, and scorecards, reading from Postgres (populated by `/ingestion`) and precomputed predictions (populated by `/ml`).

## Status (Week 3)
- `GET /health` — liveness check.
- `GET /lines` — list of in-scope Newark-area lines.
- `GET /lines/{line}/live` — most recent trip_updates reading per trip, within a 30-minute window.
- `GET /lines/{line}/predict` — v1 statistical baseline lookup for the current hour/day-of-week. Returns `{"status": "insufficient_data", ...}` honestly rather than a fabricated number when `/ml` hasn't computed a trustworthy bucket yet (true for every line right now, since ingestion has no real delay history).
- `/lines/{line}/scorecard` lands in Week 4.

Smoke-tested against a throwaway SQLite DB — including seeding a real `delay_baseline` row to confirm the `/predict` "has data" path, not just the empty-data path — all endpoints return correctly, including the 404 on an unknown line.

## Setup
```
python -m venv .venv
.venv/Scripts/activate      # .venv/bin/activate on Mac/Linux
pip install -r requirements-dev.txt   # includes test deps
cp .env.example .env         # fill in DATABASE_URL (same Supabase DB as /ingestion)
```

## Run locally
```
uvicorn main:app --reload
```
Then visit http://localhost:8000/docs for interactive API docs (FastAPI auto-generates this).

## Notes
- `models.py` is a deliberate read-side mirror of `/ingestion/models.py`, not a shared import — see the docstring in that file for why (agent ownership boundaries per `AGENTS.md`). If the DB schema changes, update both.
