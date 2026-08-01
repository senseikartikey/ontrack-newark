"""Shared configuration for the ingestion layer."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

NJT_USERNAME = os.environ.get("NJT_USERNAME", "")
NJT_PASSWORD = os.environ.get("NJT_PASSWORD", "")
NJT_RAILDATA_BASE_URL = os.environ.get(
    "NJT_RAILDATA_BASE_URL", "https://raildata.njtransit.com/api/TrainData"
)

WEATHER_USER_AGENT = os.environ.get(
    "WEATHER_USER_AGENT", "OnTrackNewark (contact: unset@example.com)"
)

# Newark, NJ coordinates -- used for the NWS grid lookup.
NEWARK_LAT = 40.7357
NEWARK_LON = -74.1724

# NWS grid for Newark, NJ, confirmed live against api.weather.gov/points on 2026-07-30.
NWS_GRID_ID = "OKX"
NWS_GRID_X = 27
NWS_GRID_Y = 42
NWS_HOURLY_FORECAST_URL = (
    f"https://api.weather.gov/gridpoints/{NWS_GRID_ID}/{NWS_GRID_X},{NWS_GRID_Y}/forecast/hourly"
)

# Static GTFS static rail feed -- public, no auth required (confirmed 2026-07-30).
NJT_STATIC_GTFS_URL = "https://www.njtransit.com/rail_data.zip"

# Newark station stop_ids, confirmed against the static GTFS feed on 2026-07-30
# (stops.txt: 106 = "NEWARK BROAD ST", 107 = "NEWARK PENN STATION").
NEWARK_STATION_STOP_IDS = {"106": "Newark Broad Street", "107": "Newark Penn Station"}

# Newark-area rail lines in scope for v1, keyed by route_short_name -- verified by
# joining stop_times.txt -> trips.txt -> routes.txt for stop_id 106 and 107 in the
# static GTFS feed on 2026-07-30 (see ENGINEERING_LOG.md). This replaces the earlier
# unconfirmed route-long-name guesses.
NEWARK_AREA_LINES = [
    "NEC",    # Northeast Corridor -- serves Newark Penn Station
    "NJCL",   # North Jersey Coast Line -- serves Newark Penn Station
    "NJCLL",  # North Jersey Coast Line (local/variant) -- serves Newark Penn Station
    "RARV",   # Raritan Valley Line -- serves Newark Penn Station
    "BNTN",   # Montclair-Boonton Line -- serves Newark Broad Street
    "BNTNM",  # Montclair-Boonton Line (variant) -- serves Newark Broad Street
    "MNE",    # Morris & Essex Line -- serves Newark Broad Street
    "MNEG",   # Gladstone Branch -- serves Newark Broad Street
]

# getVehicleData's TRAIN_LINE field uses full descriptive names that do NOT match
# static GTFS's route_short_name or even always its route_long_name exactly (e.g. the
# live feed says "Northeast Corridor Line", static GTFS route_long_name is just
# "Northeast Corridor"). Verified live on 2026-08-01 by listing every distinct
# TRAIN_LINE value across all currently-running trains system-wide (31 trains, 10
# lines) and matching against known Newark-area routes. NJCLL/BNTNM (local/variant
# short codes) have no separate live-feed name -- they map to the same TRAIN_LINE as
# their parent code, since the real-time feed doesn't distinguish local/express here.
TRAIN_LINE_TO_CODE = {
    "Northeast Corridor Line": "NEC",
    "North Jersey Coast Line": "NJCL",
    "Raritan Valley Line": "RARV",
    "Montclair-Boonton Line": "BNTN",
    "Morris & Essex Line": "MNE",
    "Gladstone Branch": "MNEG",
}


def match_line_scope(msg_line_scope: str) -> str | None:
    """Resolve a getStationMSG MSG_LINE_SCOPE value to one of our route codes.

    Verified live on 2026-08-01: real values look like "*North Jersey Coast
    Line" (leading asterisk) and "*MontClair-Boonton Line" (inconsistent
    internal casing vs. TRAIN_LINE_TO_CODE's "Montclair-Boonton Line") --
    hence a case-insensitive match after stripping the asterisk, rather than
    an exact-string dict lookup.
    """
    normalized = msg_line_scope.strip().lstrip("*").strip().lower()
    for name, code in TRAIN_LINE_TO_CODE.items():
        if name.lower() == normalized:
            return code
    return None
