# Hand-off prompt: OnTrack Newark v2, Phase 1

Paste the prompt below into a fresh Claude Code session opened in this repo (`ontrack-newark`). It's self-contained — the session doesn't need any other context from this conversation.

Phase 2+ (accounts, notifications, predictions-that-act) should be run as separate follow-up prompts once Phase 1 is verified — don't try to do it all in one pass.

---

```
You're picking up OnTrack Newark cold. Before doing anything, read CLAUDE.md, AGENTS.md, and
docs/PRD-v2.md in full — they define the project, the subagent org structure, and the v2 scope
this prompt executes. Do not skip docs/PRD-v2.md; it has the cited research behind every feature
below, and you'll need it to make good judgment calls on details this prompt doesn't spell out.

## Goal

Build Phase 1 of docs/PRD-v2.md ("Restore & Trust") — six rider-facing features that close gaps
in NJ Transit's own app, all buildable on the existing public-data architecture with no new
accounts/auth. Ship them as six separate, individually-verified units of work, not one big bang.

## How to work

Follow this repo's existing delegation model (AGENTS.md): you are acting as pm-agent, sequencing
work to the owning specialist subagent for each directory. Don't let one agent freelance outside
its lane — if a feature touches both /backend and /frontend, that's two coordinated invocations.
Check AGENTS.md's "Known limitation" note about whether custom subagent names actually resolve in
your session before assuming real delegation is happening; if they don't, do the work directly as
self-instruction and say so plainly in ENGINEERING_LOG.md, exactly as prior entries did.

After each feature lands, verify it against real data (this project's existing convention — see
recent ENGINEERING_LOG.md entries for what "verified" looks like here: real queries, real
screenshots, not just "should work") and append an ENGINEERING_LOG.md entry: what was built, what
broke and why if anything did, and the lesson worth keeping.

## The six features, in order

1. **DepartureVision-style live board** (frontend-engineer-agent)
   Restore what riders say the NJT redesign buried: a dense, scannable live board (station →
   next departures, line, scheduled vs. predicted time, delay status) as a first-class dashboard
   view, not nested behind extra navigation. Source from the existing `/live` endpoint — check
   whether it already returns everything needed grouped correctly by station, or whether it needs
   a small backend addition first.
   Acceptance: a rider can land on one view and immediately see every upcoming departure for a
   chosen Newark-area station, the way a physical station board works.

2. **"On this train" companion view** (frontend-engineer-agent, minor backend-engineer-agent)
   Given a specific live trip, show the ordered list of upcoming stops with predicted arrival
   times, so a rider mid-trip can tell when to get ready. Needs static GTFS `stop_times` for the
   trip's stop sequence joined against live position/delay data.
   Acceptance: picking any currently-active trip shows its remaining stops in order with times,
   updating as the trip progresses (respect the existing 5-minute poll cadence — don't invent a
   faster refresh than the underlying data supports).

3. **Transfer-aware Newark hub view** (frontend-engineer-agent, minor backend-engineer-agent)
   Make line-to-line transfers at Newark Penn Station / Newark Broad Street explicit and upfront,
   not something a rider has to infer. Use static GTFS to identify which lines share which Newark
   stations.
   Acceptance: viewing a Newark hub station shows, for each line passing through, what other
   lines are reachable there and roughly when the next connecting departure is.

4. **Weather-aware proactive commute advisories** (backend-engineer-agent)
   The weather data already feeds the delay-risk model but is invisible to riders. Surface it
   directly: a short, human-readable advisory (e.g. "storm expected Thursday PM rush — elevated
   delay risk on [lines]") generated from the same weather + prediction data already in Postgres.
   Acceptance: when upcoming weather conditions correlate with meaningfully elevated predicted
   risk for a line, an advisory is generated and available via the API; when conditions are
   unremarkable, no advisory is manufactured (same honesty standard as the existing
   "not enough data" behavior — don't invent urgency that isn't there).

5. **Data-confidence indicator** (data-engineer-agent, backend-engineer-agent)
   NJ Transit's own real-time data is widely distrusted by riders (see PRD-v2.md's research).
   Turn that into a differentiator: add reconciliation logic in ingestion that flags known
   anomaly patterns in the GTFS-RT feed (a trip that vanishes between polls without reaching its
   terminus, a stale timestamp that hasn't updated across multiple poll cycles, etc.), and surface
   a simple confidence signal per line/trip through the API and dashboard.
   Acceptance: the indicator is derived from real anomaly detection against the live feed (test
   it against real ingested data, not synthetic), and is honest when data looks fine — this
   should read as "we tell you when the data itself looks shaky," not a vague trust badge.

6. **Quiet Commute car lookup** (backend-engineer-agent, frontend-engineer-agent)
   Static, rule-based: NJ Transit's Quiet Commute program applies to specific NEC peak-hour
   trains. Encode the published rule set and expose a simple lookup ("does my train have a quiet
   car?") rather than trying to source this from any live feed.
   Acceptance: correct for the documented Quiet Commute train set; clearly labeled as informational
   /best-effort if NJ Transit's own published rules are themselves ambiguous or subject to change.

## Constraints (inherited from CLAUDE.md / PRD-v2.md — do not violate)

- Newark-area rail lines only. No statewide bus expansion.
- Public/documented data sources only. No scraping njtransit.com for this phase — if a feature
  needs data that isn't in GTFS-RT, static GTFS, the RailData API, or NWS weather, flag it as a
  Phase 4 feasibility question in docs/PRD-v2.md rather than building a scraper.
  Note: this phase deliberately doesn't include the Phase 4 stretch items (elevator/escalator
  status, PATH connections) — leave those alone.
  Note: this phase deliberately does NOT include accounts, auth, or notifications — that's
  Phase 2 of docs/PRD-v2.md, a separate follow-up prompt. Don't get ahead of it.
- No fabricated confidence/urgency — if data doesn't support a claim (an advisory, a confidence
  flag, a transfer time), say so honestly rather than filling the gap, matching this project's
  existing baseline/ML "not enough data" convention.
- One directory, one owning agent per change, per AGENTS.md's collaboration protocol.

## When you're done

Update CLAUDE.md's "Current status"/"What's next" section to reflect Phase 1 as shipped, and
note that Phase 2 (accounts + targeted alerts) is the next PRD-v2.md phase to pick up.
```
