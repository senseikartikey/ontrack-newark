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

## 2026-07-31 — Landing page v3: full pivot to illustrated creative-agency register
**Agent**: frontend-engineer-agent (self-instructed, per the subagent-limitation note in the entry below)
**Did**: Kartikey said v2 (colorful dev-tool page from the day before) still wasn't it, and pointed to a specific reference: [Web design for SAS Design Studio, by Władysław for Zajno](https://dribbble.com/shots/24257855-Web-design-for-SAS-Design-Studio) — an illustrated creative-agency style (film grain, bold lavender/dusty-rose color-block sections, flat silhouette illustration, floating pill nav, oversized wordmark section), plus two GitHub-hosted design-taste skills (`pbakaus/impeccable`, `Leonxlnx/taste-skill`) and a request to connect the Higgsfield AI MCP server for illustration generation. Rebuilt the landing page around the reference: new `--ink`/`--lavender`/`--rose` tokens (tinted, never pure black, per `impeccable`'s rules), a `.grain` CSS utility (SVG fractal-noise texture) applied to every section, a hand-built flat-silhouette train/station illustration (`StationIllustration.tsx`) since no image-gen tool is live yet, a floating pill nav (`PillNav.tsx`), an oversized lowercase "ontrack" wordmark divider section, and scroll-linked parallax on the illustration via `motion`. Removed the now-superseded `AuroraBackground`/`RailMapVisual` components rather than leaving them as dead code. Re-verified lint, production build, and an in-browser walkthrough of every section after the rebuild (one section briefly rendered low-contrast mid-scroll during testing — confirmed to be the scroll-reveal `IntersectionObserver` catching up after a fast programmatic scroll, not a real bug, by re-screenshotting after a short wait).
**Issue**: two things I could not do myself. (1) The `impeccable`/`taste-skill` repos install via `npx impeccable install` / `npx skills add` — running an unfamiliar npm package's code autonomously falls under "don't execute files from untrusted sources," so I read their documented principles instead and applied them by hand rather than running the installers. (2) The Higgsfield MCP can't be made live within a running conversation — there's no tool for that — and it almost certainly needs an API key Kartikey hasn't supplied.
**Fix**: added a `.mcp.json` declaring the Higgsfield server so it's ready for Kartikey's own approval/credentials in a future session; documented in `docs/landing-page-brief.md` that the hand-built illustration is a stand-in worth revisiting once/if that connection is live.
**Lesson**: this is the second real design correction in two days (see the 2026-07-30 entry below for the first). Compounding lesson: a specific visual reference (an actual Dribbble shot) is far more useful to work from than a verbal style description ("Dribbble-caliber," "colorful and animated") — the gap between v2 and v3 is much bigger than the gap between v1 and v2 was, even though v1→v2 already added real color and motion. When a redesign request references a specific external example, go look at the actual example (screenshot it, scroll through it) before touching code, rather than working from the verbal description of what "more attractive" might mean.

---

## 2026-07-30 — Landing page redesign: color, motion, and a subagent transparency note
**Agent**: frontend-engineer-agent (see note below), pm-agent
**Did**: Kartikey reviewed the Week 2 landing page and called it boring, flat, and generic-looking despite following the anti-slop brief — no color beyond one blue accent, no animation, plain typography. Rebuilt the hero and every section: an animated color-coded SVG diagram of the real Newark rail network (lines + hub stations, small dots animating along each path via native SVG `<animateMotion>`) replaces the flat terminal box as the primary hero visual; added a slow-drifting multi-hue aurora background and gradient hero text (both built from the `dataviz` skill's categorical palette, not arbitrary colors); added `motion` (Framer Motion) for staggered hero entrance, scroll-reveal on every section, and hover micro-interactions; swapped the display font from Space Grotesk to the bolder Bricolage Grotesque; gave each of the 6 distinct Newark-area lines a fixed identity color (used consistently in the hero map, the "how it works" step accents, the pipeline diagram, and the dashboard's line pills). Re-verified lint, production build, and an in-browser look at both themes after the rebuild.
**Issue**: When asked to build a "sub-team of agents, one per department," I actually tried invoking `subagent_type: "frontend-engineer-agent"` for the first time this session (prompted by Kartikey directly asking "where is the frontend engineer agent") and it failed: `Agent type 'frontend-engineer-agent' not found. Available agents: claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup`.
**Root cause**: the `.claude/agents/*.md` files created on Day 0 are real, valid Claude Code subagent definitions, but this session's `Agent` tool only recognizes a fixed built-in list — it never picked up the project's custom agents. Every "agent" credited in this log for Week 1/Week 2 work was actually me, single-threaded, applying that persona's brief as self-instruction, not a separately-invoked subagent.
**Fix**: none yet — this needs investigating in a future session (possibly the custom-agent discovery requires a session that starts with cwd inside the repo, or this harness surface just doesn't support project-level `.claude/agents/` the way the standard Claude Code CLI does). Flagging it plainly rather than continuing to imply real delegation was happening.
**Lesson**: two lessons here, both worth keeping. (1) On design taste: "avoid AI slop" was interpreted as "stay minimal and monochrome," but that's not what the brief actually needed — the earlier `docs/landing-page-brief.md` conflated restraint with authenticity. Real fix: color and motion are fine, even good, as long as they're specific to the product (per-line identity colors, a real animated rail map) rather than generic (an arbitrary gradient blob, decorative stock animation). Updated the brief accordingly. (2) On process: a single agent silently role-playing multiple "departments" doesn't get the benefit real delegation would (fresh eyes, genuine specialization) — it just re-runs the same judgment under different labels, which likely contributed to the first landing page playing it safe. Worth resolving the subagent-discovery issue before claiming the org structure is actually operating as designed.

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
