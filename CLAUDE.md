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

Week 3 done. Weather + static GTFS ingestion, backend `/lines`, `/lines/{line}/live`, and `/lines/{line}/predict` are built and verified. `/ml`'s v1 statistical baseline (delay averaged by line/hour/day-of-week) is implemented and logic-verified against synthetic data, precomputed into `delay_baseline` and served honestly (`insufficient_data` vs a real prediction) since there's no real trip history yet. The frontend (landing page + dashboard) is built and verified end-to-end, including the predicted-risk panel. `/infra` now has real GitHub Actions workflows for scheduled ingestion/baseline recomputation (previously just referenced in docs, never built). Still blocked on the user completing NJ Transit developer + Supabase signups before any of this runs against real data. See `ENGINEERING_LOG.md` for full details and the plan file for the 4-6 week build sequence.
