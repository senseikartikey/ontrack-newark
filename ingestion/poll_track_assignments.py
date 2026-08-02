"""
Entrypoint: fetch scheduled-departure track assignments for a curated set of
Newark-area / multi-track junction stations from NJT RailData's getTrainSchedule
endpoint, and log them as a time series into track_assignments.

Verified against the real API on 2026-08-02: `get_train_schedule(station)` returns
    {"STATION_2CHAR": "NP", "STATIONNAME": "Newark Penn", "STATIONMSGS": [...],
     "ITEMS": [{"SCHED_DEP_DATE": "02-Aug-2026 05:28:15 AM", "DESTINATION": "Trenton
     -SEC ✈", "TRACK": "4", "LINE": "Northeast Corrdr", "TRAIN_ID": "7813",
     "STATUS": " ", "LINECODE": "NE", "LINEABBREVIATION": "NEC",
     "STOPS": [...]}, ...]}
Real, live-confirmed findings (see ENGINEERING_LOG.md's 2026-08-02 entry for the
full writeup):
  - Newark Penn ("NP"), Newark Broad St. ("ND"), Hoboken ("HB"), and every other
    NJT-dispatched station tested came back with a real, non-empty TRACK on every
    item (e.g. "4", "1", "2", "3" at NP; "A"/"B" at Secaucus Upper Lvl).
  - New York Penn Station ("NY") came back with an *empty* TRACK on every single
    item, with no exceptions. This is expected and honest, not a bug: NY Penn is
    Amtrak-dispatched, not NJ Transit's own system, and NJT's own official data
    genuinely has no early visibility into it either -- this is exactly why
    third-party tools like nypenn.live exist to informally guess NY Penn tracks
    from historical patterns. "NY" is polled anyway (see TRACK_ASSIGNMENT_STATIONS
    in config.py) specifically to keep an honest, real historical record of
    whether/when that ever changes, which is valuable information on its own.

Station identity here is NJT RailData's own 2-character station code (e.g. "NP"),
a THIRD station-identifier space in this codebase -- distinct from both
TripUpdate.stop_id (the live vehicle feed's station *name* strings, e.g.
"Newark Penn Station") and the static GTFS `stops` table's numeric stop_id (e.g.
"107"). None of the three share a key. See models.py's TrackAssignment docstring
and config.py's TRACK_ASSIGNMENT_STATIONS comment for more.

Time-series design (not upsert-by-train-id): the same scheduled train
(station_code, train_id, scheduled_time) is expected to be observed on many poll
cycles as its departure approaches, and the entire point -- especially for "NY" --
is to see whether/when its track value *changes*. Overwriting prior observations
in place would destroy that signal. Instead, _should_insert() below only writes a
new row when the observed track differs from the most recent one on file for that
exact (station_code, train_id, scheduled_time) triple, or when MIN_REOBSERVE_INTERVAL
has elapsed since the last observation -- so an unchanged, still-empty "NY" row
gets a periodic honest checkpoint rather than either silence or a duplicate row on
every 5-minute poll cycle.

Run on the same schedule as poll_gtfs_rt.py (every 5 min) by the GitHub Actions
workflow in /.github/workflows/ -- see /infra/README.md and this module's own
entry in ENGINEERING_LOG.md for the requested workflow change (devops-engineer-agent
owns /infra and /.github/workflows/, not this directory).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from config import TRACK_ASSIGNMENT_STATIONS
from db import get_session, init_db
from models import TrackAssignment
from njt_client import NJTransitRailClient

# Same NJT local-timestamp format/timezone as poll_gtfs_rt.py's SCHED_DEP_TIME --
# getTrainSchedule's SCHED_DEP_DATE uses the identical "02-Aug-2026 05:28:15 AM"
# shape (US Eastern local time).
_NJT_TZ = ZoneInfo("America/New_York")
_NJT_TIME_FORMAT = "%d-%b-%Y %I:%M:%S %p"

# Floor between re-recording an *unchanged* track value for the same scheduled
# train -- long enough to avoid a duplicate near-identical row every single 5-minute
# poll, short enough to still produce a real, honest periodic checkpoint (useful
# for "NY" specifically: proves the logging mechanism is alive and still seeing
# genuinely empty tracks, not that polling silently stopped).
MIN_REOBSERVE_INTERVAL = timedelta(minutes=30)


def _parse_njt_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        naive = datetime.strptime(value, _NJT_TIME_FORMAT)
    except ValueError:
        return None
    return naive.replace(tzinfo=_NJT_TZ)


def _normalize(value) -> str | None:
    """Trims whitespace and turns an empty/missing field into a clean None rather
    than an empty string -- matters most for TRACK (see module docstring: an empty
    TRACK is an honest, meaningful value for "NY", not missing data, but should
    still be stored as NULL rather than "" for a consistent nullable column)."""
    if value is None:
        return None
    trimmed = str(value).strip()
    return trimmed or None


def _extract_items(station_code: str, response: dict) -> list[dict]:
    items = response.get("ITEMS") or []
    parsed = []
    for item in items:
        train_id = _normalize(item.get("TRAIN_ID"))
        scheduled_time = _parse_njt_time(item.get("SCHED_DEP_DATE"))
        if not train_id or scheduled_time is None:
            continue
        parsed.append(
            {
                "train_id": train_id,
                "line": _normalize(item.get("LINE")),
                "destination": _normalize(item.get("DESTINATION")),
                "track": _normalize(item.get("TRACK")),
                "scheduled_time": scheduled_time,
            }
        )
    return parsed


def _load_latest_by_key(
    session, station_code: str, train_ids: set[str]
) -> dict[tuple[str, datetime], TrackAssignment]:
    """Most recent TrackAssignment row on file for each (train_id, scheduled_time)
    at this station, in one query per station rather than one query per item --
    the comparison _should_insert() needs to decide whether this poll's reading is
    new information worth logging."""
    if not train_ids:
        return {}
    rows = (
        session.execute(
            select(TrackAssignment)
            .where(
                TrackAssignment.station_code == station_code,
                TrackAssignment.train_id.in_(train_ids),
            )
            .order_by(TrackAssignment.observed_at.desc())
        )
        .scalars()
        .all()
    )
    latest: dict[tuple[str, datetime], TrackAssignment] = {}
    for row in rows:
        key = (row.train_id, row.scheduled_time)
        if key not in latest:  # rows are already ordered newest-first
            latest[key] = row
    return latest


def _should_insert(prior: TrackAssignment | None, new_track: str | None, now: datetime) -> bool:
    """See module docstring's "Time-series design" section for the rationale."""
    if prior is None:
        return True
    if (prior.track or None) != (new_track or None):
        return True
    return now - prior.observed_at >= MIN_REOBSERVE_INTERVAL


def run() -> int:
    init_db()
    client = NJTransitRailClient()
    now = datetime.now(timezone.utc)
    rows_written = 0
    rows_seen = 0
    stations_ok = 0
    stations_failed = []

    with get_session() as session:
        for station_code, expected_name in TRACK_ASSIGNMENT_STATIONS.items():
            try:
                response = client.get_train_schedule(station_code)
            except Exception as e:  # noqa: BLE001 -- one station's failure shouldn't abort the rest
                stations_failed.append(station_code)
                print(f"[poll_track_assignments] {station_code}: request failed: {e}")
                continue

            station_name = _normalize(response.get("STATIONNAME")) or expected_name
            items = _extract_items(station_code, response)
            rows_seen += len(items)
            stations_ok += 1

            train_ids = {i["train_id"] for i in items}
            latest_by_key = _load_latest_by_key(session, station_code, train_ids)

            for i in items:
                key = (i["train_id"], i["scheduled_time"])
                prior = latest_by_key.get(key)
                if not _should_insert(prior, i["track"], now):
                    continue

                row = TrackAssignment(
                    station_code=station_code,
                    station_name=station_name,
                    train_id=i["train_id"],
                    line=i["line"],
                    destination=i["destination"],
                    track=i["track"],
                    scheduled_time=i["scheduled_time"],
                    observed_at=now,
                )
                session.add(row)
                rows_written += 1
                # Keep the in-memory view current in case the same key somehow
                # appears twice in one response -- avoids a redundant duplicate
                # insert within a single poll cycle.
                latest_by_key[key] = row

    print(
        f"[poll_track_assignments] polled {stations_ok}/{len(TRACK_ASSIGNMENT_STATIONS)} "
        f"stations, saw {rows_seen} scheduled items, wrote {rows_written} new/changed "
        f"track_assignment rows"
    )
    if stations_failed:
        print(f"[poll_track_assignments] failed stations: {', '.join(stations_failed)}")
    return rows_written


if __name__ == "__main__":
    run()
