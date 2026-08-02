"""
Entrypoint: fetch live NJ Transit rail vehicle data and upsert delay readings into
trip_updates. Run on a schedule (every 5 min) by the GitHub Actions workflow in /infra.

Verified against the real API on 2026-08-01 (Kartikey's RailData access was
approved). `get_vehicle_data()` returns a bare list of dicts like:
    {"ID": "67", "TRAIN_LINE": "Main Line", "DIRECTION": "Westbound",
     "ICS_TRACK_CKT": "RJ-193-1TK", "LAST_MODIFIED": "31-Jul-2026 10:39:10 PM",
     "SCHED_DEP_TIME": "31-Jul-2026 10:42:45 PM", "SEC_LATE": "32",
     "NEXT_STOP": "Ridgewood", "LONGITUDE": "-74.120592", "LATITUDE": "40.980629"}

Confirmed live by listing every distinct TRAIN_LINE across all currently-running
trains system-wide -- see config.py's TRAIN_LINE_TO_CODE for the verified mapping
from these full descriptive names to our route_short_name codes.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.postgresql import insert

from config import TRAIN_LINE_TO_CODE
from db import get_session, init_db
from models import TripUpdate
from njt_client import NJTransitRailClient
from reconcile_anomalies import reconcile as reconcile_anomalies

# NJT's timestamps are US Eastern local time, formatted like "31-Jul-2026 10:42:45 PM".
_NJT_TZ = ZoneInfo("America/New_York")
_NJT_TIME_FORMAT = "%d-%b-%Y %I:%M:%S %p"


def _parse_njt_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        naive = datetime.strptime(value, _NJT_TIME_FORMAT)
    except ValueError:
        return None
    return naive.replace(tzinfo=_NJT_TZ)


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_trip_updates(trains: list[dict]) -> list[dict]:
    """Filter live vehicle data down to Newark-area lines and normalize field names.

    Note on `stop_id`: NEXT_STOP is a human-readable station name (e.g. "Ridgewood"),
    not the numeric stop_id static GTFS uses (e.g. "107") -- the two ID systems don't
    line up, and there's no reliable join key without a name-matching layer we haven't
    built. We store the station name as-is; it's more immediately useful to a reader
    than an opaque numeric ID would be anyway.
    """
    updates = []
    for train in trains:
        code = TRAIN_LINE_TO_CODE.get(train.get("TRAIN_LINE", ""))
        if code is None:
            continue

        scheduled_time = _parse_njt_time(train.get("SCHED_DEP_TIME"))
        if scheduled_time is None:
            continue

        delay_seconds = _to_int(train.get("SEC_LATE"))
        actual_time = (
            scheduled_time + timedelta(seconds=delay_seconds)
            if delay_seconds is not None
            else scheduled_time
        )

        updates.append(
            {
                "trip_id": str(train.get("ID", "")),
                "line": code,
                "direction": train.get("DIRECTION"),
                "stop_id": train.get("NEXT_STOP"),
                "scheduled_time": scheduled_time,
                "actual_time": actual_time,
                "delay_seconds": delay_seconds,
            }
        )
    return updates


def run() -> int:
    init_db()
    client = NJTransitRailClient()
    trains = client.get_vehicle_data()
    updates = _extract_trip_updates(trains)
    now = datetime.now(timezone.utc)
    rows_written = 0

    with get_session() as session:
        # Reconcile against DB state from prior polls *before* writing this
        # poll's own rows, so "the previous poll" in the comparison means the
        # actual previous poll, not the one about to be inserted below. See
        # reconcile_anomalies.py's module docstring for the detection logic.
        anomaly_summary = reconcile_anomalies(session, updates, now)

        for u in updates:
            if not u["trip_id"] or not u["stop_id"]:
                continue
            stmt = insert(TripUpdate).values(
                trip_id=u["trip_id"],
                line=u["line"],
                direction=u["direction"],
                stop_id=u["stop_id"],
                scheduled_time=u["scheduled_time"],
                actual_time=u["actual_time"],
                delay_seconds=u["delay_seconds"],
                collected_at=now,
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["trip_id", "stop_id", "collected_at"]
            )
            session.execute(stmt)
            rows_written += 1

    print(f"[poll_gtfs_rt] wrote {rows_written} trip update rows (of {len(trains)} total trains system-wide)")
    print(
        f"[poll_gtfs_rt] anomaly reconciliation: "
        f"{anomaly_summary['vanished_mid_route']} vanished_mid_route, "
        f"{anomaly_summary['stale_timestamp']} stale_timestamp"
    )
    return rows_written


if __name__ == "__main__":
    run()
