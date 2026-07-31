"""
Entrypoint: fetch live NJ Transit rail vehicle data and upsert delay readings into
trip_updates. Run on a schedule (every 60-120s) by the GitHub Actions workflow in /infra.

STATUS: blocked on real NJT RailData API credentials/response shape. The parsing logic
below (`_extract_trip_updates`) is a best-effort placeholder based on the field names
NJT's API is commonly documented to use (trip/train ID, line, station, scheduled vs.
estimated time). Once NJT_USERNAME/NJT_PASSWORD are set and njt_client.py's endpoints
are confirmed (see its TODOs), run this once, print the raw response, and correct
`_extract_trip_updates` to match the actual JSON shape before trusting its output.
"""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from config import NEWARK_AREA_LINES
from db import get_session, init_db
from models import TripUpdate
from njt_client import NJTransitRailClient


def _extract_trip_updates(raw: dict) -> list[dict]:
    """Turn the raw NJT vehicle-data response into a flat list of trip update dicts.

    TODO(data-engineer-agent): replace this once the real response shape is known.
    Placeholder assumes something like {"TRAIN_DATA": [{"TRAIN_ID", "LINE", "STATION",
    "SCHED_DEP_DATE", "SEC_LATE", ...}, ...]} based on commonly-referenced NJT field
    naming conventions -- NOT verified.
    """
    updates = []
    for train in raw.get("TRAIN_DATA", []):
        line = train.get("LINE") or train.get("LINEABBREVIATION")
        if NEWARK_AREA_LINES and line not in NEWARK_AREA_LINES:
            continue
        updates.append(
            {
                "trip_id": str(train.get("TRAIN_ID", "")),
                "line": line,
                "direction": train.get("DIRECTION"),
                "stop_id": train.get("STATION") or train.get("STATION_2CHAR"),
                "scheduled_time": train.get("SCHED_DEP_DATE"),
                "actual_time": train.get("STATION_POSITION") or train.get("SCHED_DEP_DATE"),
                "delay_seconds": _to_int(train.get("SEC_LATE")),
            }
        )
    return updates


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def run() -> int:
    init_db()
    client = NJTransitRailClient()
    raw = client.get_vehicle_data()
    updates = _extract_trip_updates(raw)
    now = datetime.now(timezone.utc)
    rows_written = 0

    with get_session() as session:
        for u in updates:
            if not u["trip_id"] or not u["scheduled_time"]:
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

    print(f"[poll_gtfs_rt] wrote {rows_written} trip update rows")
    return rows_written


if __name__ == "__main__":
    run()
