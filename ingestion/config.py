"""Shared configuration for the ingestion layer."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

NJT_USERNAME = os.environ.get("NJT_USERNAME", "")
NJT_PASSWORD = os.environ.get("NJT_PASSWORD", "")
NJT_RAILDATA_BASE_URL = os.environ.get(
    "NJT_RAILDATA_BASE_URL", "https://raildata.njtransit.com/api"
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

# Newark-area rail lines in scope for v1. These are NJ Transit's public line names;
# once the static GTFS feed is loaded (Week 2), cross-check these against the feed's
# actual route_id/route_short_name values and update NEWARK_AREA_LINES accordingly --
# matching by name substring here is a best-effort placeholder, not a confirmed mapping.
NEWARK_AREA_LINES = [
    "Northeast Corridor",
    "North Jersey Coast Line",
    "Raritan Valley Line",
    "Morristown Line",
    "Gladstone Branch",
    "Montclair-Boonton Line",
]

# The two Newark rail stations most riders care about for this project.
NEWARK_STATIONS = ["Newark Penn Station", "Newark Broad Street"]
