"""
Data-confidence indicator (docs/PRD-v2.md Phase 1: "NJT's own feed is widely
distrusted -- vehicles appear/disappear from tracking, schedules show
already-departed trains"). Surfaces /ingestion's `feed_anomalies` table
(populated by reconcile_anomalies.py, run inside every poll_gtfs_rt.py
invocation) as a per-line reliability signal.

Deliberately reports specific, real detected anomaly types/counts rather than
a synthesized "trust score" -- consistent with this project's honesty
convention (see routers/lines.py's get_current_risk() and routers/advisories.py
for the same pattern: an explicit `status` plus real numbers, never a vague
composite metric). "No anomalies found" and "no live data to evaluate" are
kept as two distinct states (see `status` below) precisely because collapsing
them would itself be a fabricated-confidence bug: an ingestion outage (no
polls landing at all) must not read as "the feed looks reliable."
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import RAIL_LINES
from db import get_db
from models import FeedAnomaly, TripUpdate
from routers.lines import LIVE_WINDOW_MINUTES

router = APIRouter(prefix="/lines", tags=["data-confidence"])

# How far back to look for feed_anomalies rows when judging "has the live feed
# looked reliable *recently*." Anomalies are written by reconcile_anomalies.py
# roughly once per poll cycle (every 5 min in production, per
# infra/'s "Ingest live data" schedule), so 3 hours spans several dozen poll
# cycles -- long enough that a single transient reading isn't over- or
# under-weighted by chance, but short enough that this answers "does the feed
# look flaky right now," not "did it ever have a bad day" (an anomaly from
# many hours ago may already be resolved on NJT's end, and reporting it
# forever would be its own kind of dishonesty).
ANOMALY_WINDOW_HOURS = 3

# How many of the most recent anomalies (within the window) to return as
# concrete examples when issues are detected -- gives riders/devs something
# specific to look at instead of just a count, matching the "don't manufacture
# a vague trust score" instruction.
MAX_RECENT_EXAMPLES = 5

KNOWN_ANOMALY_TYPES = ("vanished_mid_route", "stale_timestamp")


@router.get("/{line}/data-confidence")
def get_data_confidence(line: str, db: Session = Depends(get_db)):
    """
    `status`:
      - "unknown": no `trip_updates` row for this line within the last
        `LIVE_WINDOW_MINUTES` (the same "is the feed currently live" window
        `/live` uses) -- there's no recent polling activity to evaluate
        reliability against, so anomaly counts (even if zero) can't honestly
        be read as "the feed looks fine." This is the expected state during
        an ingestion outage.
      - "ok": recent polling activity exists and zero `feed_anomalies` rows
        were recorded for this line in the last `ANOMALY_WINDOW_HOURS`.
      - "issues_detected": recent polling activity exists and at least one
        `feed_anomalies` row was recorded in the window -- `anomaly_counts`
        and `recent_anomalies` give the specifics.
    """
    if line not in RAIL_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    now = datetime.now(timezone.utc)

    last_poll_at = db.execute(
        select(func.max(TripUpdate.collected_at)).where(TripUpdate.line == line)
    ).scalar()

    feed_is_live = (
        last_poll_at is not None
        and (now - last_poll_at) <= timedelta(minutes=LIVE_WINDOW_MINUTES)
    )

    window_cutoff = now - timedelta(hours=ANOMALY_WINDOW_HOURS)
    anomaly_rows = db.execute(
        select(FeedAnomaly)
        .where(FeedAnomaly.line == line, FeedAnomaly.detected_at >= window_cutoff)
        .order_by(FeedAnomaly.detected_at.desc())
    ).scalars().all()

    anomaly_counts = {t: 0 for t in KNOWN_ANOMALY_TYPES}
    for row in anomaly_rows:
        anomaly_counts[row.anomaly_type] = anomaly_counts.get(row.anomaly_type, 0) + 1
    total_anomalies = len(anomaly_rows)

    base = {
        "line": line,
        "as_of": now,
        "window_hours": ANOMALY_WINDOW_HOURS,
        "last_poll_at": last_poll_at,
    }

    if not feed_is_live:
        return {
            **base,
            "status": "unknown",
            "message": (
                "No recent live-feed activity for this line "
                f"(last poll: {last_poll_at.isoformat() if last_poll_at else 'never'}) -- "
                "not enough current data to say whether the feed looks reliable."
            ),
            "anomaly_counts": anomaly_counts,
            "total_anomalies": total_anomalies,
            "recent_anomalies": [],
        }

    if total_anomalies == 0:
        return {
            **base,
            "status": "ok",
            "message": (
                f"No known feed issues for this line in the last {ANOMALY_WINDOW_HOURS}h "
                "-- no vanished-trip or stale-reading patterns detected."
            ),
            "anomaly_counts": anomaly_counts,
            "total_anomalies": 0,
            "recent_anomalies": [],
        }

    type_summary = ", ".join(
        f"{count} {atype}" for atype, count in anomaly_counts.items() if count > 0
    )
    return {
        **base,
        "status": "issues_detected",
        "message": (
            f"Live feed for this line has looked unreliable in the last "
            f"{ANOMALY_WINDOW_HOURS}h: {type_summary}."
        ),
        "anomaly_counts": anomaly_counts,
        "total_anomalies": total_anomalies,
        "recent_anomalies": [
            {
                "trip_id": r.trip_id,
                "anomaly_type": r.anomaly_type,
                "detected_at": r.detected_at,
                "detail": r.detail,
            }
            for r in anomaly_rows[:MAX_RECENT_EXAMPLES]
        ],
    }
