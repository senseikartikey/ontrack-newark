# CLAUDE.md

Project context for Claude Code (and any human collaborator) working in this repo.

## What this is

**OnTrack Newark** — a live reliability dashboard + predictive delay-risk tool for NJ Transit rail lines serving Newark (Northeast Corridor, Morris & Essex/Gladstone, etc.) into NYC. It ingests NJ Transit's public GTFS-RT feed and weather data, predicts delay risk for upcoming departures, and shows historical on-time scorecards per line. Public data only, no PII.

Built as a portfolio/showcase project (meetups, conferences) with a real path to becoming a small product later.

## Architecture at a glance

```
GTFS-RT + GTFS static + weather  →  /ingestion  →  Postgres (Supabase)
                                                        │
                                          /ml  (baseline + LightGBM, precomputed)
                                                        │
                                          /backend (FastAPI, reads DB + predictions)
                                                        │
                                          /frontend (Next.js: dashboard + landing page)
```

## Directory map → agent ownership

| Directory | Owning agent | What lives there |
|---|---|---|
| `/ingestion` | `data-engineer-agent` | GTFS-RT poller, static GTFS loader, weather fetcher, DB models/migrations |
| `/backend` | `backend-engineer-agent` | FastAPI app: routers, prediction-serving, caching |
| `/ml` | `ml-engineer-agent` | Feature engineering, baseline model, LightGBM training, evaluation |
| `/frontend` | `frontend-engineer-agent` | Next.js app: dashboard + landing page |
| `/infra` | `devops-engineer-agent` | GitHub Actions workflows, Render/Vercel/Supabase config |
| `docs/`, `README.md` | `docs-writer-agent` | Architecture diagrams, demo script |
| root docs (this file, `AGENTS.md`, etc.) | `pm-agent` | Kept current as the project evolves |

Full agent roles and when to invoke each one: see [`AGENTS.md`](AGENTS.md).
Reusable project workflows (deploy checks, data verification, demo prep): see [`SKILLS.md`](SKILLS.md).
Running history of what was built and what broke: see [`ENGINEERING_LOG.md`](ENGINEERING_LOG.md).

## Conventions

- **Commits**: imperative, present tense, scoped (`ingestion: add GTFS-RT poller`, `frontend: build hero section`). One logical change per commit.
- **Directories stay owned**: work inside `/ingestion` goes through `data-engineer-agent`, etc. Don't let one agent freelance in another's directory — if a change spans two, do it as two coordinated invocations.
- **No secrets committed**: NJ Transit API keys, weather API keys, and DB connection strings live in `.env` (gitignored) locally and in the hosting provider's secret manager in deployment. `.env.example` documents required vars.
- **Every meaningful unit of work gets an `ENGINEERING_LOG.md` entry** — especially anything that broke and got fixed. This is the project's memory across sessions.

## How to run locally

- `/ingestion`: see `/ingestion/README.md`.
- `/backend`: see `/backend/README.md`.
- `/ml`: see `/ml/README.md`.
- `/frontend`: see `/frontend/README.md`.
- Scheduled jobs (production): see `/infra/README.md`.

## Current status

**Live on real infrastructure.** Repo: [github.com/senseikartikey/ontrack-newark](https://github.com/senseikartikey/ontrack-newark) (public). Supabase Postgres is connected (via the pooler endpoint — the direct connection is IPv6-only and fails from GitHub Actions runners, see `ENGINEERING_LOG.md` for that bug). Weather and static GTFS ingestion run for real, both locally and on a schedule via GitHub Actions (`Ingest live data` every 5 min, `Refresh static GTFS` weekly, `Recompute delay baseline` daily — all three confirmed passing by run ID, not just triggered). Backend (`/lines`, `/live`, `/predict`) and the frontend (landing page v3 + dashboard with predicted-risk panel) are built and verified against this real database.

**Remaining blocker**: NJ Transit RailData API approval (submitted 2026-07-31, ~2-3 days) — this is the only thing standing between the current infrastructure and real rail delay data (and therefore a real ML model, since `/ml`'s baseline has nothing to compute from yet). Once approved, resolve the TODOs in `/ingestion/njt_client.py` and `poll_gtfs_rt.py` against the real API reference.

See `ENGINEERING_LOG.md` for full details and the plan file for the 4-6 week build sequence.
