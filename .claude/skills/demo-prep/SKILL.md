---
name: demo-prep
description: Rehearsal checklist for showing OnTrack Newark live at a meetup/conference — confirms the stack is up, data is fresh, and walks the demo script. Use the day before a talk, not the morning of.
---

# demo-prep

1. Run `/ingest-verify` first — a demo on stale/empty data is worse than no demo.
2. Confirm the deployed URLs are live: landing page (Vercel), dashboard, and backend API health endpoint. If running locally instead, start `/backend` and `/frontend` and confirm they talk to each other.
3. Open `docs/demo-script.md` and walk through it end to end exactly as it will be presented: landing page → "how it works" → dashboard → live line → predicted risk → historical scorecard.
4. Time the walkthrough. Flag anything that's slow enough to be awkward live (a cold-start API call, a slow chart render) so `backend-engineer-agent`/`frontend-engineer-agent` can address it before the real thing.
5. Have a fallback ready: a screenshot or short recording of the dashboard in case of venue wifi issues, since the live demo depends on real external APIs (NJ Transit, weather) being reachable.

If `docs/demo-script.md` doesn't exist yet, that's `docs-writer-agent`'s task — flag it rather than improvising the script during prep.
