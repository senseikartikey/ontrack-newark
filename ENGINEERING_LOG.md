# Engineering Log

Running, dated history of what was built and what was learned. Newest entry on top. One entry per meaningful unit of work — especially anything that broke.

**Entry format:**
```
## YYYY-MM-DD — <short title>
**Agent**: <which subagent, or "pm"/"kartikey">
**Did**: <what was built/changed>
**Issue**: <what broke, if anything — omit if nothing broke>
**Root cause**: <why it broke>
**Fix**: <what resolved it>
**Lesson**: <what to do differently next time — this is the part worth keeping>
```

---

## 2026-07-30 — Week 1 kickoff: ingestion + backend scaffolds
**Agent**: data-engineer-agent, backend-engineer-agent
**Did**:
- `/ingestion`: DB models (`trip_updates`, `weather_hourly`, `service_alerts`), NWS weather client + poller (verified live against `api.weather.gov` — 156 hourly periods fetched and parsed correctly for Newark's grid point OKX/27,42), and a scaffolded NJ Transit RailData client + poller.
- `/backend`: FastAPI app with `/health`, `/lines`, `/lines/{line}/live`, smoke-tested end-to-end against a throwaway SQLite DB (all endpoints, including the 404 path, behave correctly).
**Issue**: NJ Transit's RailData API has no publicly-visible documentation — the reference client (`github.com/jtarrio/raildata`) confirms the auth *pattern* (username/password → bearer token, auto-refreshed) but not exact endpoint paths or response field names. The full API reference is only visible after registering at developer.njtransit.com.
**Root cause**: NJT gates its API docs behind developer account registration; no public mirror of the reference exists.
**Fix**: Wrote `njt_client.py`/`poll_gtfs_rt.py` as a structurally-correct scaffold (token caching/refresh, clean request methods) with every unconfirmed endpoint path and response field explicitly marked `TODO` rather than silently guessing and hoping. Shipped and verified the weather half of ingestion fully, since that API is public and needed no guesswork.
**Lesson**: When a required external API's docs are gated behind an account we don't have yet, don't fabricate exact request/response shapes — scaffold the correct *pattern* with loud TODOs instead. It keeps the code honest and makes the follow-up work (once Kartikey registers and can see the real docs) a quick fill-in rather than a debugging session against silently wrong assumptions.

**Manual follow-up needed from Kartikey** (see `/ingestion/README.md` for full steps):
1. Register at https://developer.njtransit.com/registration/ for RailData API access; add credentials to `/ingestion/.env`.
2. Once registered, resolve the `TODO`s in `njt_client.py`/`poll_gtfs_rt.py` against the real API reference.
3. Create a free Supabase project; add the Postgres connection string to `/ingestion/.env` and `/backend/.env`.

---

## 2026-07-30 — Repo scaffold (Day 0)
**Agent**: pm-agent
**Did**: Created the `ontrack-newark` repo structure (`/ingestion`, `/backend`, `/ml`, `/frontend`, `/infra`), wrote `CLAUDE.md`, `AGENTS.md`, `SKILLS.md`, this log, the 8 `.claude/agents/*.md` subagent definitions, and the 3 `.claude/skills/*` workflows (`deploy-check`, `ingest-verify`, `demo-prep`). No feature code yet.
**Lesson**: Setting up the org/tooling scaffold before any feature work means every subsequent agent invocation has a stable place to get context from (`CLAUDE.md` + `AGENTS.md`) instead of re-deriving project structure each time. Worth the up-front time given agents start cold on every call.
