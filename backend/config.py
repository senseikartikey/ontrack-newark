import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# Mirrors /ingestion/config.py's TRAIN_LINE_TO_CODE's set of in-scope route codes --
# kept in sync manually, see the note in backend/models.py about why these aren't
# shared via cross-directory import. Statewide expansion (2026-08-02): widened from
# 8 to all 14 heavy/commuter-rail route codes now covered by ingestion (see
# i-am-not-happy-pure-aurora.md step 4 and ENGINEERING_LOG.md), deliberately
# excluding the 3 light-rail routes also present in the static `routes` table
# (HBLR, NLR, RVLN) per an explicit user decision. Renamed from NEWARK_AREA_LINES
# to RAIL_LINES (plan step 6) now that the scope is statewide, not Newark-area --
# pure rename, no behavior change.
RAIL_LINES = [
    "NEC", "NJCL", "NJCLL", "RARV", "BNTN", "BNTNM", "MNE", "MNEG",
    "MNBN", "ATLC", "MNBNP", "MRL", "PASC", "PRIN",
]

# route_short_name -> route_long_name, queried fresh from the real static GTFS
# `routes` table (2026-08-02) rather than guessed -- see ENGINEERING_LOG.md. Values
# match routes.long_name verbatim for consistency with the original 8-line entries
# below (which already mirror long_name exactly, e.g. "Northeast Corridor" not
# "Northeast Corridor Line"). Two notable cases where the static long_name diverges
# from the live feed's own naming (see ingestion/config.py's TRAIN_LINE_TO_CODE
# comments for the live-side strings) -- static long_name is used here anyway, to
# keep this dict internally consistent and because ingestion's dict is the one that
# needs to track the live feed's exact strings, not this one:
#   - ATLC: static long_name is "Atlantic City Rail Line"; the live feed's
#     TRAIN_LINE string is "Atlantic City Line" (no "Rail").
#   - MNBN: static combines two live-feed lines ("Main Line" and "Bergen County
#     Line") into one route, long_name "Main/Bergen County Line".
LINE_DISPLAY_NAMES = {
    "NEC": "Northeast Corridor",
    "NJCL": "North Jersey Coast Line",
    "NJCLL": "North Jersey Coast Line",
    "RARV": "Raritan Valley Line",
    "BNTN": "Montclair-Boonton Line",
    "BNTNM": "Montclair-Boonton Line",
    "MNE": "Morris & Essex Line",
    "MNEG": "Gladstone Branch",
    "MNBN": "Main/Bergen County Line",
    "ATLC": "Atlantic City Rail Line",
    "MNBNP": "Port Jervis Line",
    "MRL": "Meadowlands Rail Line",
    "PASC": "Pascack Valley Line",
    "PRIN": "Princeton Shuttle",
}

# Mirrors /ml/config.py's risk thresholds -- see that file for reasoning.
RISK_LOW_MAX_SECONDS = 120
RISK_MEDIUM_MAX_SECONDS = 300

# Mirrors /ingestion/config.py's TRACK_ASSIGNMENT_STATIONS exactly (station_code ->
# expected station display name), kept in sync manually per this file's existing
# mirror convention (see the RAIL_LINES comment above and backend/models.py's docstring
# for why /backend doesn't cross-import /ingestion code). Used by
# routers/stations.py's board-enrichment join to resolve a live-feed station name
# (GET /stations/{station_name}/board's TripUpdate.stop_id-based param) to the
# track_assignments table's station_code -- a case-insensitive name lookup, not a
# numeric one, since none of this codebase's three station-identifier spaces share a
# key. If NJT RailData's real STATIONNAME for a code ever differs from the name below,
# the affected station just won't resolve a track_code (departures fall back to
# track: null) rather than joining on the wrong station -- see routers/stations.py.
# NJT RailData's 2-character station code for New York Penn Station -- mirrors
# /ml/config.py's NY_PENN_STATION_CODE. Used as the default/documented target of
# GET /stations/{station_code}/predicted-tracks (routers/stations.py), the only
# station /ml's compute_track_predictions.py currently computes predictions for.
NY_PENN_STATION_CODE = "NY"

# How many hours ahead of "now" GET /stations/{station_code}/predicted-tracks looks
# for upcoming track_assignments rows -- a reasonable "what's coming up soon" window,
# not tied to any official NJT/Amtrak schedule-visibility horizon (there isn't one
# published). See routers/stations.py for the small backward grace window also
# applied so a train scheduled moments ago (still boarding) isn't dropped.
PREDICTED_TRACKS_WINDOW_HOURS = 3

TRACK_ASSIGNMENT_STATIONS = {
    "NP": "Newark Penn Station",
    "ND": "Newark Broad Street",
    "HB": "Hoboken",
    "SE": "Secaucus Upper Lvl",
    "TS": "Secaucus Lower Lvl",
    "NB": "New Brunswick",
    "MP": "Metropark",
    "RH": "Rahway",
    "EZ": "Elizabeth",
    "TR": "Trenton",
    "LB": "Long Branch",
    "DO": "Dover",
    "ST": "Summit",
    "CN": "Convent Station",
    "MR": "Morristown",
    "PJ": "Princeton Junction",
    "NY": "New York Penn Station",  # NJT-official data has no visibility into NY Penn
    # tracks either (Amtrak-dispatched) -- track is expected null here on essentially
    # every real row. See models.py's TrackAssignment docstring.
}
