# Demo Script — OnTrack Newark

For meetups/conferences. Run `/demo-prep` the day before, not the morning of.

## Setup before you start
- Confirm both servers are running (`/ingestion` schedule doesn't need anything from you — it's already live in GitHub Actions).
- Have the landing page and dashboard both open in tabs.
- Have `github.com/senseikartikey/ontrack-newark` open in a third tab, on the Actions page (shows the real scheduled runs) or `ENGINEERING_LOG.md`.

## The walkthrough (~5 minutes)

**1. Open the landing page.** Don't explain it — let it sit for a second. Point out it's not a mockup: the hero panel is live, reading from the real API right now.

> "This is OnTrack Newark. I ride NJ Transit rail into Newark, and like everyone else here, I've stood on a platform finding out my train is late only after I'm already late. NJ Transit's own real-time feed already knows a train is running behind — it just never tells you *before* you leave the house. So I built the layer that does."

**2. Scroll to "how it works."** Point at the pipeline list.

> "Ingest → predict → display. Every 5 minutes, a scheduled job pulls NJ Transit's real GTFS-RT feed and weather data into Postgres. A statistical model — soon a real ML model — scores upcoming departures for delay risk. The backend serves it, the frontend shows it."

**3. Click through to the dashboard.** Pick a line with visible live data.

> "This is real, right now — not a demo dataset. [point at a trip row] This train's actual next stop is [whatever it says]. [point at delay] Real delay, in real time."

**4. Point at the predicted risk panel.**
- If it says "insufficient data": *"This is the honest part — the model won't guess until it has enough real history to be right more often than not. That's a deliberate choice, not a limitation I'm hiding."*
- If it shows a risk level: *"Historically, this line around this hour runs about N minutes late — that's the forward-looking piece most transit apps don't have."*

**5. Point at the scorecard + alerts.**

> "Rolling on-time percentage, and real service alerts pulled straight from NJ Transit — not scraped, their actual alerting API."

**6. Close on the GitHub repo / engineering log.**

> "Everything here is public — the code, and an engineering log of every bug I hit building it, including a few genuinely interesting ones: NJ Transit's real-time feed names lines completely differently than their published schedule data, and Supabase's default connection string doesn't even work from GitHub's own CI runners. That log is as much the point of this project as the dashboard is."

## Anticipated questions
- **"Is this deployed somewhere I can check later?"** — be honest about current state (see root README's "What's next"); if not yet public, offer to run it locally for them or share the repo.
- **"How accurate is the prediction?"** — give the real MAE/accuracy once the v2 model ships; until then, say plainly that v1 is a statistical baseline and the honest evaluation is coming once there's enough data.
- **"Why NJ Transit specifically?"** — the founder-note answer: you ride these lines, the data is public and good, nobody had built the forward-looking layer.

## Fallback
If the venue wifi is bad or the API is briefly down, the dashboard's own honest empty/error states are the fallback — they're designed to degrade gracefully, so even "it's not connected right now" reads as intentional, not broken. Have a couple of screenshots saved locally as a last resort.
