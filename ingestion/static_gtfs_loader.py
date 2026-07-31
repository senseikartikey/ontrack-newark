"""
Entrypoint: download NJ Transit's public static rail GTFS feed and load routes/stops
reference data into Postgres. This feed is genuinely public -- no registration or API
key required (confirmed 2026-07-30, see ENGINEERING_LOG.md) -- unlike the GTFS-RT
RailData API in njt_client.py.

Run infrequently (weekly is plenty; this data changes rarely), not on the same tight
schedule as poll_gtfs_rt.py/poll_weather.py.
"""
import csv
import io
import zipfile

import requests
from sqlalchemy.dialects.postgresql import insert

from config import NJT_STATIC_GTFS_URL
from db import get_session, init_db
from models import Route, Stop


def _download_gtfs_zip() -> zipfile.ZipFile:
    resp = requests.get(NJT_STATIC_GTFS_URL, headers={"User-Agent": "OnTrackNewark/1.0"}, timeout=30)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))


def _read_csv(z: zipfile.ZipFile, filename: str) -> list[dict]:
    with z.open(filename) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


def run() -> dict:
    init_db()
    z = _download_gtfs_zip()
    routes = _read_csv(z, "routes.txt")
    stops = _read_csv(z, "stops.txt")

    routes_written = 0
    stops_written = 0

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

    print(f"[static_gtfs_loader] upserted {routes_written} routes, {stops_written} stops")
    return {"routes": routes_written, "stops": stops_written}


if __name__ == "__main__":
    run()
