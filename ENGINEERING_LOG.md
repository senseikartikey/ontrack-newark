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

## 2026-07-30 — Week 2: static GTFS, corrected line codes, frontend build
**Agent**: data-engineer-agent, backend-engineer-agent, frontend-engineer-agent
**Did**:
- Discovered NJ Transit's static rail GTFS feed (`https://www.njtransit.com/rail_data.zip`) is genuinely public — no auth required, unlike the GTFS-RT RailData API. Downloaded and parsed it for real.
- Used the real `routes.txt`/`stops.txt`/`stop_times.txt`/`trips.txt` to **replace guessed line names with verified data**: joined stop_times → trips → routes for Newark Penn Station (stop_id 107) and Newark Broad Street (stop_id 106) to get the actual route_short_name codes serving each station (NEC/NJCL/NJCLL/RARV at Penn; BNTN/BNTNM/MNE/MNEG at Broad St). Updated `NEWARK_AREA_LINES` in both `/ingestion/config.py` and `/backend/config.py` accordingly.
- Built and verified `/ingestion/static_gtfs_loader.py` (Route/Stop reference tables) against the real downloaded feed (17 routes, 231 stops parsed correctly).
- Updated `/backend`'s `/lines` endpoint to return `{code, display_name}` using a verified route_short_name → route_long_name mapping; re-verified all endpoints still pass.
- Scaffolded `/frontend` (Next.js, TypeScript, Tailwind via `create-next-app`). Built the landing page per `docs/landing-page-brief.md` and a dashboard shell polling the live backend. Design tokens use the `dataviz` skill's validated palette, with status colors mapped to on-time/delay semantics.
- Verified everything for real: `npm run lint` and `npm run build` both pass clean; ran the production build and the FastAPI backend together locally, loaded both pages in-browser (dark and light theme), and confirmed the dashboard's line picker and live-status table genuinely round-trip through the real API — not just visually inspected.
**Issue**: `create-next-app`'s new `react-hooks/set-state-in-effect` lint rule flagged the first draft of `ThemeToggle.tsx` (calling `setState` synchronously inside a `useEffect` to hydrate theme from `localStorage`).
**Root cause**: that pattern is exactly what the rule exists to catch — `localStorage` is external state, and synchronizing external state into React via an effect-that-calls-setState causes an extra render pass; React's own guidance is to use `useSyncExternalStore` for this case instead.
**Fix**: rewrote `ThemeToggle` around `useSyncExternalStore` (subscribing to a custom event + the native `storage` event) with a plain DOM-sync effect for the `data-theme` attribute — no setState-in-effect, lint clean.
**Lesson**: when a static/public data source dependency turns out to be genuinely public (like the static GTFS feed vs. the gated RailData API), verify it immediately by actually downloading and parsing it rather than assuming the same access barrier applies everywhere — it upgraded several "TODO, unconfirmed" placeholders from Week 1 to verified facts and unblocked real Week 2 work without needing the still-pending NJT account.

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
