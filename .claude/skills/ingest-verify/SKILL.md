---
name: ingest-verify
description: Sanity-checks the OnTrack Newark ingestion pipeline's latest data — freshness, row counts, and gaps per line. Use before trusting the ML pipeline or before a live demo.
---

# ingest-verify

Confirms the data pipeline is actually alive and producing usable data, not just "deployed."

1. **Freshness**: query the most recent `collected_at` timestamp in `trip_updates`. If it's older than ~2x the polling interval, the GitHub Actions ingestion workflow is likely broken or paused — check its run history.
2. **Volume**: count rows ingested in the last 24 hours, broken down by line. Any Newark-area line with zero rows in that window is a red flag — check whether that line's GTFS-RT feed changed its trip ID format or route naming.
3. **Weather freshness**: confirm `weather_hourly` has an entry within the last 2 hours.
4. **Schema sanity**: spot-check a handful of recent `trip_updates` rows for obviously bad values — negative delays beyond a plausible range, null `line`, timestamps in the future.
5. Report findings as a short table: line, last-seen timestamp, row count (24h), status (OK / STALE / EMPTY).

If anything is STALE or EMPTY, don't proceed to a demo or a model retrain until `data-engineer-agent` has fixed it — a demo on stale data undercuts the whole pitch.
