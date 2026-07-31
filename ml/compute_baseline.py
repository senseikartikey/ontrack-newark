"""
Entrypoint: recompute the v1 statistical delay baseline from all observed
trip_updates and upsert into delay_baseline. Run on a schedule (daily is plenty --
the underlying distribution shifts slowly) by the GitHub Actions workflow in /infra.

Aggregation is done in Python, not SQL, deliberately: Postgres's EXTRACT(DOW) uses a
Sunday=0 convention, while Python's datetime.weekday() uses Monday=0 -- doing the
grouping here keeps the write side and the backend's read side (which uses
datetime.weekday() against "now") trivially consistent, and at current/expected data
volumes there's no performance reason to push this into SQL instead.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from config import MIN_SAMPLES_THRESHOLD
from db import get_session, init_db
from models import DelayBaseline, TripUpdate


@dataclass
class _Bucket:
    total_delay: int = 0
    count: int = 0
    trip_ids: set = field(default_factory=set)


def run() -> dict:
    init_db()
    buckets: dict[tuple[str, int, int], _Bucket] = defaultdict(_Bucket)

    with get_session() as session:
        rows = session.execute(
            select(
                TripUpdate.line,
                TripUpdate.trip_id,
                TripUpdate.scheduled_time,
                TripUpdate.delay_seconds,
            ).where(TripUpdate.delay_seconds.is_not(None))
        ).all()

        for line, trip_id, scheduled_time, delay_seconds in rows:
            key = (line, scheduled_time.hour, scheduled_time.weekday())
            bucket = buckets[key]
            # One prediction input per trip, not per repeated GTFS-RT reading of
            # the same trip -- otherwise a trip polled every 90s for 10 minutes
            # would count as 6-7 samples instead of 1.
            if trip_id in bucket.trip_ids:
                continue
            bucket.trip_ids.add(trip_id)
            bucket.total_delay += delay_seconds
            bucket.count += 1

        now = datetime.now(timezone.utc)
        written = 0
        skipped_low_sample = 0

        for (line, hour_of_day, day_of_week), bucket in buckets.items():
            if bucket.count < MIN_SAMPLES_THRESHOLD:
                skipped_low_sample += 1
                continue
            avg_delay = bucket.total_delay / bucket.count
            stmt = insert(DelayBaseline).values(
                line=line,
                hour_of_day=hour_of_day,
                day_of_week=day_of_week,
                avg_delay_seconds=avg_delay,
                sample_size=bucket.count,
                computed_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["line", "hour_of_day", "day_of_week"],
                set_={
                    "avg_delay_seconds": avg_delay,
                    "sample_size": bucket.count,
                    "computed_at": now,
                },
            )
            session.execute(stmt)
            written += 1

    print(
        f"[compute_baseline] wrote {written} buckets, "
        f"skipped {skipped_low_sample} below the {MIN_SAMPLES_THRESHOLD}-sample threshold"
    )
    return {"written": written, "skipped_low_sample": skipped_low_sample}


if __name__ == "__main__":
    run()
