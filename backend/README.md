# /backend

Owned by `backend-engineer-agent`. FastAPI app serving live status, predictions, and scorecards, reading from Postgres (populated by `/ingestion`) and precomputed predictions (populated by `/ml`).

## Status (Week 1)
- `GET /health` — liveness check.
- `GET /lines` — list of in-scope Newark-area lines.
- `GET /lines/{line}/live` — most recent trip_updates reading per trip, within a 30-minute window.
- `/lines/{line}/predict` and `/lines/{line}/scorecard` land in Week 3-4 once `/ml` exists.

Smoke-tested against a throwaway SQLite DB (empty-data paths only, since no real trip data exists yet) — all endpoints return correctly, including the 404 on an unknown line.

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
