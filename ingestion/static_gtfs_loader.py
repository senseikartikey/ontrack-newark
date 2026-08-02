"""
Entrypoint: download NJ Transit's public static rail GTFS feed and load
routes/stops/trips/stop_times reference data into Postgres. This feed is genuinely
public -- no registration or API key required (confirmed 2026-07-30, see
ENGINEERING_LOG.md) -- unlike the GTFS-RT RailData API in njt_client.py.

Run infrequently (weekly is plenty; this data changes rarely), not on the same tight
schedule as poll_gtfs_rt.py/poll_weather.py.

trips.txt/stop_times.txt give the ordered stop sequence per trip (needed for the
"on this train" companion view and the Newark-hub transfer view -- see
docs/PRD-v2.md). stop_times.txt is large enough on the real feed (~46k rows,
confirmed 2026-08-01) that row-at-a-time upserts over a remote Supabase connection
are impractically slow, so it's upserted in chunked batches; routes/stops/trips stay
row-at-a-time since they're small enough (tens to low thousands of rows) not to
matter.
"""
import csv
import io
import zipfile

import requests
from sqlalchemy.dialects.postgresql import insert

from config import NJT_STATIC_GTFS_URL
from db import get_session, init_db
from models import Route, Stop, StopTime, Trip

# stop_times.txt is tens of thousands of rows on the real feed -- upsert in chunks
# rather than one session.execute() per row (network round-trip cost dominates
# against a remote Supabase connection).
STOP_TIMES_BATCH_SIZE = 1000


def _download_gtfs_zip() -> zipfile.ZipFile:
    resp = requests.get(NJT_STATIC_GTFS_URL, headers={"User-Agent": "OnTrackNewark/1.0"}, timeout=30)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))


def _read_csv(z: zipfile.ZipFile, filename: str) -> list[dict]:
    with z.open(filename) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def run() -> dict:
    init_db()
    z = _download_gtfs_zip()
    routes = _read_csv(z, "routes.txt")
    stops = _read_csv(z, "stops.txt")
    trips = _read_csv(z, "trips.txt")
    stop_times = _read_csv(z, "stop_times.txt")

    routes_written = 0
    stops_written = 0
    trips_written = 0
    stop_times_written = 0

    with get_session() as session:
        for r in routes:
            stmt = insert(Route).values(
                route_id=r["route_id"],
                short_name=r["route_short_name"],
                long_name=r["route_long_name"],
                color=r.get("route_color"),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Route.route_id],
                set_={
                    "short_name": r["route_short_name"],
                    "long_name": r["route_long_name"],
                    "color": r.get("route_color"),
                },
            )
            session.execute(stmt)
            routes_written += 1

        for s in stops:
            lat = float(s["stop_lat"]) if s.get("stop_lat") else None
            lon = float(s["stop_lon"]) if s.get("stop_lon") else None
            stmt = insert(Stop).values(
                stop_id=s["stop_id"],
                stop_name=s["stop_name"],
                lat=lat,
                lon=lon,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Stop.stop_id],
                set_={"stop_name": s["stop_name"], "lat": lat, "lon": lon},
            )
            session.execute(stmt)
            stops_written += 1

        for t in trips:
            stmt = insert(Trip).values(
                trip_id=t["trip_id"],
                route_id=t["route_id"],
                service_id=t["service_id"],
                trip_headsign=t.get("trip_headsign") or None,
                direction_id=t.get("direction_id") or None,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Trip.trip_id],
                set_={
                    "route_id": t["route_id"],
                    "service_id": t["service_id"],
                    "trip_headsign": t.get("trip_headsign") or None,
                    "direction_id": t.get("direction_id") or None,
                },
            )
            session.execute(stmt)
            trips_written += 1

        for batch in _chunks(stop_times, STOP_TIMES_BATCH_SIZE):
            rows = [
                {
                    "trip_id": st["trip_id"],
                    "stop_sequence": int(st["stop_sequence"]),
                    "stop_id": st["stop_id"],
                    "arrival_time": st.get("arrival_time") or None,
                    "departure_time": st.get("departure_time") or None,
                }
                for st in batch
            ]
            stmt = insert(StopTime)
            stmt = stmt.on_conflict_do_update(
                index_elements=[StopTime.trip_id, StopTime.stop_sequence],
                set_={
                    "stop_id": stmt.excluded.stop_id,
                    "arrival_time": stmt.excluded.arrival_time,
                    "departure_time": stmt.excluded.departure_time,
                },
            )
            session.execute(stmt, rows)
            stop_times_written += len(rows)

    print(
        f"[static_gtfs_loader] upserted {routes_written} routes, {stops_written} stops, "
        f"{trips_written} trips, {stop_times_written} stop_times"
    )
    return {
        "routes": routes_written,
        "stops": stops_written,
        "trips": trips_written,
        "stop_times": stop_times_written,
    }


if __name__ == "__main__":
    run()
