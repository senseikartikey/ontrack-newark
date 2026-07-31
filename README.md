# OnTrack Newark

A live reliability dashboard and predictive delay-risk tool for NJ Transit rail lines serving Newark (Northeast Corridor, Morris & Essex/Gladstone, etc.) into NYC. Built on NJ Transit's public GTFS-RT feed and weather data — public data only, no PII.

**Status**: Day 0 — repo and project tooling scaffolded, feature build starting per the plan.

## What it does (target state)
- **Live status** for active trips, from GTFS-RT trip updates.
- **Predicted delay risk** for upcoming departures, using historical patterns, weather, and active service alerts.
- **Historical reliability scorecards** (7/30-day on-time %) per line.
- A public landing page telling the story of the project.

## Project structure
```
/ingestion   → data ingestion (GTFS-RT, static GTFS, weather)
/backend     → FastAPI app
/ml          → prediction models + evaluation
/frontend    → Next.js dashboard + landing page
/infra       → deployment configs
```

See [`CLAUDE.md`](CLAUDE.md) for full architecture context, [`AGENTS.md`](AGENTS.md) for the engineering org structure, [`SKILLS.md`](SKILLS.md) for reusable workflows, and [`ENGINEERING_LOG.md`](ENGINEERING_LOG.md) for a running history of what's been built.

## Setup
Per-layer setup instructions will be added here as each layer is scaffolded (see the build sequence in the project plan).
