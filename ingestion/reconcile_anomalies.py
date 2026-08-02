"""
Anomaly-reconciliation logic for the live GTFS-RT feed's reliability.

Called from poll_gtfs_rt.py's run(), inside the same DB session, right after
the current poll's vehicle data is fetched but *before* this poll's rows are
inserted -- each poll is a fresh script invocation with no in-process memory
of past runs, so "was this trip active last cycle, and has it changed since"
has to be answered by querying Postgres for what previous polls wrote, not by
holding state in the process. Running the queries before this poll's insert
is what makes "the previous poll" mean the actual previous poll rather than
the one about to be written.

Detects two known unreliability patterns riders/NJT itself report in the live
feed (see docs/PRD-v2.md's "Data-confidence indicator" research: vehicles
appear/disappear from tracking, and schedules show already-departed trains):

1. **vanished_mid_route**: a trip that was still expected to be running as of
   the previous poll (its own last-reported next-stop ETA hadn't passed yet)
   simply disappears from the live response on this poll, with no plausible
   reason to believe it already completed its route.
2. **stale_timestamp**: a trip keeps appearing across several consecutive
   polls, but its scheduled_time/actual_time/delay_seconds never change,
   despite collected_at advancing each time -- suggesting the feed is
   serving a cached reading for that trip rather than a fresh one.

Anomalies are written to the additive `feed_anomalies` table (models.py) --
this module never touches trip_updates.

Known limitation (documented rather than silently assumed away): NJ Transit's
live vehicle feed reports NEXT_STOP (the train's *next* stop), not its final
terminus, and its trip "ID" field doesn't share a key with static GTFS's
trip_id (see poll_gtfs_rt.py's docstring) -- so there is no ground truth here
for "has this trip actually reached the end of its scheduled route."
vanished_mid_route uses the best available proxy instead: whether the train's
own last-reported next-stop ETA (actual_time = scheduled_time + delay) had
already passed by the time it was last seen. If it hadn't passed, the trip's
disappearance can't be explained as an ordinary "it finished its trip and
stopped broadcasting" -- that's exactly the pattern worth flagging.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from models import FeedAnomaly, TripUpdate

# Only compare against "the previous poll" if it happened recently enough that
# a poll-to-poll comparison is still meaningful. If the last poll on record was
# e.g. hours ago (a CI outage, or the first run in a while), a trip's absence
# now says nothing about the live feed's reliability -- skip rather than risk
# a flood of false positives from a stale reference point.
MAX_PREVIOUS_POLL_GAP = timedelta(minutes=20)

# Small grace period so a trip whose next-stop ETA was only seconds away as of
# the last poll isn't flagged just for plausibly reaching that stop and being
# dropped from the feed in the few minutes before this poll ran.
VANISH_GRACE_PERIOD = timedelta(minutes=1)

# How many consecutive polls (this one + prior ones) must show byte-identical
# scheduled_time/actual_time/delay_seconds before it's treated as staleness
# rather than coincidence -- a train legitimately sitting exactly on schedule
# with 0s delay for one poll is normal; the same exact reading 3+ polls running
# is not.
STALE_MIN_CONSECUTIVE_POLLS = 3


def _recent_poll_gap_ok(previous_poll_at: datetime | None, now: datetime) -> bool:
    if previous_poll_at is None:
        return False
    return (now - previous_poll_at) <= MAX_PREVIOUS_POLL_GAP


def detect_vanished_trips(session, current_updates: list[dict], now: datetime) -> list[dict]:
    """Flag trips seen on the previous poll, still expected to be en route as of
    that poll (per VANISH_GRACE_PERIOD), that are completely absent from this
    poll's live response."""
    previous_poll_at = session.execute(
        select(TripUpdate.collected_at).order_by(TripUpdate.collected_at.desc()).limit(1)
    ).scalar()

    if not _recent_poll_gap_ok(previous_poll_at, now):
        return []

    current_trip_ids = {u["trip_id"] for u in current_updates if u["trip_id"]}

    previous_rows = session.execute(
        select(TripUpdate.trip_id, TripUpdate.line, TripUpdate.actual_time).where(
            TripUpdate.collected_at == previous_poll_at
        )
    ).all()

    anomalies = []
    already_flagged_this_run: set[str] = set()  # a trip can have >1 row per poll (multiple stop_id readings)
    for trip_id, line, actual_time in previous_rows:
        if trip_id in current_trip_ids or trip_id in already_flagged_this_run:
            continue
        if actual_time is None:
            continue
        # still expected to be en route as of the previous poll -- its own
        # reported next-stop ETA (schedule + delay) hadn't passed yet
        if actual_time > previous_poll_at + VANISH_GRACE_PERIOD:
            already_flagged_this_run.add(trip_id)
            remaining_seconds = int((actual_time - previous_poll_at).total_seconds())
            anomalies.append(
                {
                    "trip_id": trip_id,
                    "line": line,
                    "anomaly_type": "vanished_mid_route",
                    "detected_at": now,
                    "detail": (
                        f"last seen at {previous_poll_at.isoformat()} with next-stop ETA "
                        f"{actual_time.isoformat()} (still {remaining_seconds}s out); "
                        f"absent from the feed on this poll"
                    ),
                }
            )
    return anomalies


def detect_stale_trips(session, current_updates: list[dict], now: datetime) -> list[dict]:
    """Flag trips whose scheduled_time/actual_time/delay_seconds haven't changed
    across STALE_MIN_CONSECUTIVE_POLLS consecutive polls despite collected_at
    advancing each time."""
    anomalies = []

    for update in current_updates:
        trip_id = update["trip_id"]
        if not trip_id:
            continue

        prior_rows = session.execute(
            select(
                TripUpdate.collected_at,
                TripUpdate.scheduled_time,
                TripUpdate.actual_time,
                TripUpdate.delay_seconds,
            )
            .where(TripUpdate.trip_id == trip_id)
            .order_by(TripUpdate.collected_at.desc())
            .limit(STALE_MIN_CONSECUTIVE_POLLS - 1)
        ).all()

        # not enough poll history yet for this trip to call it a pattern
        if len(prior_rows) < STALE_MIN_CONSECUTIVE_POLLS - 1:
            continue

        unchanged = all(
            r.scheduled_time == update["scheduled_time"]
            and r.actual_time == update["actual_time"]
            and r.delay_seconds == update["delay_seconds"]
            for r in prior_rows
        )
        if not unchanged:
            continue

        # collected_at must genuinely be distinct across all of these polls --
        # guards against counting the same poll's data twice
        collected_ats = {r.collected_at for r in prior_rows} | {now}
        if len(collected_ats) < STALE_MIN_CONSECUTIVE_POLLS:
            continue

        earliest_unchanged_at = min(r.collected_at for r in prior_rows)

        # don't re-flag every single poll for the life of an ongoing stall --
        # only flag once per stall episode (i.e. skip if already flagged since
        # this exact unchanged streak began)
        already_flagged = session.execute(
            select(FeedAnomaly.id)
            .where(FeedAnomaly.trip_id == trip_id)
            .where(FeedAnomaly.anomaly_type == "stale_timestamp")
            .where(FeedAnomaly.detected_at >= earliest_unchanged_at)
            .limit(1)
        ).first()
        if already_flagged:
            continue

        anomalies.append(
            {
                "trip_id": trip_id,
                "line": update["line"],
                "anomaly_type": "stale_timestamp",
                "detected_at": now,
                "detail": (
                    f"scheduled_time/actual_time/delay_seconds unchanged across "
                    f"{STALE_MIN_CONSECUTIVE_POLLS} consecutive polls since "
                    f"{earliest_unchanged_at.isoformat()} (delay_seconds={update['delay_seconds']})"
                ),
            }
        )
    return anomalies


def record_anomalies(session, anomalies: list[dict]) -> int:
    for a in anomalies:
        session.execute(insert(FeedAnomaly).values(**a))
    return len(anomalies)


def reconcile(session, current_updates: list[dict], now: datetime) -> dict:
    """Run both detectors and persist any findings. Must be called with the
    same session poll_gtfs_rt.py is about to use for this poll's own insert,
    and before that insert happens (see module docstring)."""
    vanished = detect_vanished_trips(session, current_updates, now)
    stale = detect_stale_trips(session, current_updates, now)
    written = record_anomalies(session, vanished + stale)
    return {
        "vanished_mid_route": len(vanished),
        "stale_timestamp": len(stale),
        "written": written,
    }
