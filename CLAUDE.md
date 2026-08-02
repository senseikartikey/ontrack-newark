# CLAUDE.md

Project context for Claude Code (and any human collaborator) working in this repo.

## What this is

**OnTrack** — fixes what NJ Transit's own app gets wrong, for every heavy-rail line in New Jersey (14 lines statewide as of 2026-08-02, not just Newark-area ones). NJ Transit's app buries its own live departure board, doesn't show transfers up front, and only tells you a train is late after you're already on the platform. OnTrack combines the features scattered across NJ Transit's app and third-party alternatives — a real live board, a transfer lookup, a trip companion view — into one place, and predicts delay risk before you leave the house instead of just reporting it after the fact. See [`docs/PRD-v2.md`](docs/PRD-v2.md) for the full research behind this positioning and [`ENGINEERING_LOG.md`](ENGINEERING_LOG.md) for the statewide-expansion/rebrand entries (2026-08-02).

**v2 direction**: on top of the public-data core above, v2 adds lightweight user accounts (email-based, via Supabase Auth) so personalization (saved lines, targeted push/email alerts) is possible — see `docs/PRD-v2.md`'s Phase 2.

Data sources stay public/documented only (GTFS-RT, static GTFS, RailData API, NWS weather). PII stays minimal by design: v2 accounts are email-only, and there is **no payment data, no ticketing, no government ID** — that would require an official NJT commercial partnership and PCI-DSS scope, explicitly out of scope for this project.

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

**Week 5 done, full endpoint set live.** Repo: [github.com/senseikartikey/ontrack-newark](https://github.com/senseikartikey/ontrack-newark) (public). Supabase Postgres connected (pooler endpoint). NJ Transit RailData access approved 2026-08-01 — real GTFS-RT delay data, service alerts, weather, and static GTFS are all flowing into production on schedule via GitHub Actions (`Ingest live data` every 5 min, `Refresh static GTFS` weekly, `Recompute delay baseline` daily). Backend now serves the full planned endpoint set (`/lines`, `/live`, `/predict`, `/scorecard`, `/alerts`); frontend (landing page v4 + dashboard with predicted-risk, scorecard, and alerts panels) verified against real data. Root `README.md` has a real architecture diagram; `docs/demo-script.md` exists for conference use.

**v2 model pipeline built** (`ml/train_model.py`, `ml/features.py`) and logic-verified against synthetic data (model clearly beat a synthetic baseline in a controlled test). Runs daily via GitHub Actions alongside the baseline recompute; correctly detects real data is still far below the training threshold (47 rows vs. a 500-row minimum) and skips itself rather than training garbage. Backend's `/predict` already prefers a v2 prediction over the baseline whenever one exists, so no further backend work is needed once real training succeeds.

**v2 Phase 1 ("Restore & Trust") shipped, 2026-08-01.** All six features from `docs/PRD-v2.md`'s Phase 1 are live: a DepartureVision-style live board (`/board`, `GET /stations`, `GET /stations/{station_name}/board`), an "on this train" companion view (`/trips/[tripId]`, `GET /trips/{trip_id}/upcoming-stops`), a transfer-aware Newark hub view (`/hub`, `GET /stations/{stop_id}/transfers` — verified Newark Broad Street and Newark Penn Station resolve to completely non-overlapping, geographically correct line sets), weather-aware commute advisories (`GET /lines/{line}/advisory`), a data-confidence indicator surfaced on the dashboard (`GET /lines/{line}/data-confidence`, backed by new GTFS-RT feed-anomaly reconciliation in `/ingestion`), and a best-effort Quiet Commute car lookup (`GET /trips/{trip_id}/quiet-commute`). Also extended the static GTFS loader to load `trips.txt`/`stop_times.txt` (previously only `routes`/`stops`), which the stop-sequence features needed. Two real ID-space mismatches were discovered and honestly worked around rather than silently assumed to line up: live `trip_updates.trip_id` doesn't correspond to static GTFS `trips.trip_id` (companion view uses a schedule-proximity match, clearly labeled `match_type` in the API response), same pattern as the earlier-discovered `stop_id`-vs-station-name mismatch. Most frontend views could not be visually verified in-browser (no browser-automation tool was available in the sessions that built them) — verified instead via real API calls, type-checking against real response shapes, and lint/build passing; said so plainly in each `ENGINEERING_LOG.md` entry rather than claiming an unperformed visual check.

**Known issue found during this build, not yet fixed**: NJ Transit's RailData API auth endpoint (`getToken`) was returning `500` for the entire build session — confirmed via `gh run list --workflow=ingest.yml`, every scheduled `Ingest live data` run failing identically. This is an NJT-side outage, not a bug in this codebase, but it means production's live data has been stale and `delay_baseline` is currently empty (0 rows for any line/hour/day-of-week bucket), which also silently affects the existing `/predict` endpoint. Worth checking NJT's API status and re-verifying ingestion once it's confirmed recovered — the code is ready to resume working automatically, no code change needed, just confirmation the upstream outage has cleared.

**What's next**:
- **Immediate**: confirm the NJT RailData outage above has cleared, and once fresh data accumulates, do the in-browser visual verification pass the build session couldn't (multi-line board rendering, hub view, trip companion view, data-confidence badge states, Quiet Commute badge).
- ML: purely a waiting game — once enough real trip history accumulates, `train_model.py`'s next scheduled run will train for real and start serving v2 predictions automatically — no manual step required.
- Deployment: no public hosted URL yet — backend/frontend deployment (Render/Railway + Vercel) was never actually done despite being in the original plan; still local-only. See root `README.md`'s "What's next."
- Scope: **`docs/PRD-v2.md` Phase 2** ("Personalize" — accounts via Supabase Auth, saved lines/stations, targeted push/email alerts) is next, once Phase 1 has had real-data visual verification.

See `ENGINEERING_LOG.md` for full details and the plan file for the 4-6 week build sequence.
