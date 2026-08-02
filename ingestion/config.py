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

# Rail lines in scope for v1 (originally scoped to lines serving the two Newark hub
# stations), keyed by route_short_name -- verified by joining stop_times.txt ->
# trips.txt -> routes.txt for stop_id 106 and 107 in the static GTFS feed on
# 2026-07-30 (see ENGINEERING_LOG.md). This replaces the earlier unconfirmed
# route-long-name guesses. NOTE: superseded by TRAIN_LINE_TO_CODE below for the
# statewide expansion (2026-08-02) -- this list is currently unused within
# /ingestion (poll_gtfs_rt.py filters via TRAIN_LINE_TO_CODE directly) and still
# reflects the original 8-line scope rather than the full 14-line statewide set.
RAIL_LINES = [
    "NEC",    # Northeast Corridor
    "NJCL",   # North Jersey Coast Line
    "NJCLL",  # North Jersey Coast Line (local/variant)
    "RARV",   # Raritan Valley Line
    "BNTN",   # Montclair-Boonton Line
    "BNTNM",  # Montclair-Boonton Line (variant)
    "MNE",    # Morris & Essex Line
    "MNEG",   # Gladstone Branch
]

# getVehicleData's TRAIN_LINE field uses full descriptive names that do NOT match
# static GTFS's route_short_name or even always its route_long_name exactly (e.g. the
# live feed says "Northeast Corridor Line", static GTFS route_long_name is just
# "Northeast Corridor"). NJCLL/BNTNM (local/variant short codes) have no separate
# live-feed name -- they map to the same TRAIN_LINE as their parent code, since the
# real-time feed doesn't distinguish local/express here.
#
# Statewide expansion (2026-08-02): scope is all 14 heavy/commuter-rail routes in the
# static `routes` table, deliberately EXCLUDING the 3 light-rail routes also present
# there (HBLR Hudson-Bergen LR, NLR Newark Light Rail, RVLN River LINE) -- light rail
# is out of scope per an explicit user decision (see
# i-am-not-happy-pure-aurora.md and its correction of an earlier "all 17 routes"
# miscount). Each entry below is tagged with its real provenance:
#   - "live-verified <date>": the exact TRAIN_LINE string was observed in a real
#     getVehicleData() response on that date.
#   - "DERIVED, UNVERIFIED": no live train for that route happened to be running
#     during any session's scan window, so the value is a best-effort guess from the
#     static routes.route_long_name, not a confirmed live-feed string. These will
#     silently fail to match (dropped by _extract_trip_updates(), same as any
#     unmapped line) until a real train on that route is caught in a future scan and
#     the guess is confirmed or corrected.
TRAIN_LINE_TO_CODE = {
    # -- Live-verified 2026-08-01 (original 10-line/31-train system-wide scan),
    # re-confirmed live again 2026-08-02 (10-train scan, off-peak ~2:20am ET).
    "Northeast Corridor Line": "NEC",
    "North Jersey Coast Line": "NJCL",
    "Raritan Valley Line": "RARV",
    "Morris & Essex Line": "MNE",
    "Gladstone Branch": "MNEG",
    # -- Live-verified 2026-08-01 only (not re-seen in the 2026-08-02 scan, but
    # already confirmed real -- a route not running at 2am doesn't un-verify it).
    "Montclair-Boonton Line": "BNTN",
    # -- MNBN ("Main/Bergen County Line" in static GTFS) is reported by the live feed
    # as two separate TRAIN_LINE names, both live-verified 2026-08-01 and re-confirmed
    # 2026-08-02 -- static GTFS combines them into one route, the live feed doesn't.
    "Main Line": "MNBN",
    "Bergen County Line": "MNBN",
    # -- Newly live-verified 2026-08-02 (Atlantic City Line was not running during the
    # original 2026-08-01 scan). NOTE: the real live TRAIN_LINE string is "Atlantic
    # City Line", NOT "Atlantic City Rail Line" -- differs from static GTFS's
    # route_long_name ("Atlantic City Rail Line"), same kind of live/static mismatch
    # already seen with NEC. Confirms guessing from route_long_name isn't reliable,
    # which is exactly why the four entries below are flagged unverified rather than
    # silently trusted.
    "Atlantic City Line": "ATLC",
    # -- DERIVED from static routes.route_long_name, UNVERIFIED against the live feed.
    # None of these had a train running system-wide during the 2026-08-02 ~2:20am ET
    # scan (only 10 trains total, system-wide, at that hour) or the 2026-08-01 scan.
    # Given the ATLC mismatch just above, treat these as genuinely unconfirmed --
    # they may silently fail to match real TRAIN_LINE strings until corrected against
    # a real scan that happens to catch a train on each route.
    "Port Jervis Line": "MNBNP",  # static long_name for MNBNP; UNVERIFIED
    "Meadowlands Rail Line": "MRL",  # static long_name for MRL; UNVERIFIED --
    # MetLife-event-only service, may need a scan during an actual event to confirm
    "Pascack Valley Line": "PASC",  # static long_name for PASC; UNVERIFIED
    "Princeton Shuttle": "PRIN",  # static long_name for PRIN; UNVERIFIED --
    # colloquially "the Dinky" in the real world; if this guess doesn't match, that's
    # the next thing to try
}


# Station codes polled by poll_track_assignments.py's getTrainSchedule-based track
# logging. This is NJT RailData's own 2-character station-code space (e.g. "NP" for
# Newark Penn Station) -- distinct from both TRAIN_LINE_TO_CODE's live-feed station
# *names* (used for TripUpdate.stop_id) and static GTFS's numeric stop_id. See
# poll_track_assignments.py's module docstring and ENGINEERING_LOG.md's 2026-08-02
# entry for the full story.
#
# All 17 codes below were empirically confirmed against the real getTrainSchedule
# endpoint on 2026-08-02 (each returned a real, non-empty ITEMS list under its
# expected station name) -- see ENGINEERING_LOG.md for exact verification detail.
# Source for the code->name mapping itself: cross-checked against the full station
# table in the public reference client github.com/jtarrio/raildata's codes.go
# (already used successfully for other endpoint shapes in this codebase -- see
# njt_client.py's module docstring), not guessed from a naming pattern.
#
# Scope is deliberately narrow, not the full ~231-row static `stops` table: only
# stations where a track assignment is actually meaningful information (multi-track
# junctions/major interchanges), per an explicit scoping decision -- most NJT
# stations are single-platform, where "the track" is not actually in question. "NY"
# (New York Penn Station) is included even though its TRACK values are expected to
# come back empty on essentially every observation -- see TrackAssignment's
# docstring in models.py for why that's a real, valuable negative finding
# (Amtrak-dispatched, no NJT early visibility) rather than something to work around.
TRACK_ASSIGNMENT_STATIONS = {
    "NP": "Newark Penn Station",
    "ND": "Newark Broad Street",
    "HB": "Hoboken",
    "SE": "Secaucus Upper Lvl",
    "TS": "Secaucus Lower Lvl",  # aka Secaucus Junction -- NEC through-tracks,
    # a distinct real code from "SE" above; both are genuinely different platforms.
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
    "PJ": "Princeton Junction",  # NEC junction with the Princeton Branch ("the Dinky")
    "NY": "New York Penn Station",  # always included -- see module comment above.
    # -- UNVERIFIED entries, added 2026-08-02. Codes sourced from cross-referencing
    # chexedy/whereisnjtransit's station table (that repo has no LICENSE file, so
    # only the factual code->name mapping is used here, not any of its code/JSON
    # copied wholesale -- station codes are NJ Transit's own operational
    # identifiers, not that repo author's creative work). NOT empirically confirmed
    # against the live getTrainSchedule endpoint (blocked by the exhausted daily
    # quota all day 2026-08-02) -- verify each for real the next time the quota is
    # available, the same way the 17 entries above were confirmed one-by-one.
    "DV": "Denville",  # per whereisnjtransit; unverified
    "NT": "Netcong",  # per whereisnjtransit; unverified
    "RA": "Raritan",  # per whereisnjtransit; unverified
    "CH": "South Amboy",  # per whereisnjtransit; code has no obvious relation to the
    # station name (unlike the other three), extra reason for caution -- verify this
    # one first when quota allows, it's the most likely to be wrong.
}


# Resolution note, 2026-08-02: the four candidates identified below (real
# NJT rail-geography junctions -- DENVILLE where Montclair-Boonton converges
# onto the Morristown Line, NETCONG where the Morristown Line branches to its
# Lake Hopatcong/Hackettstown termini, SOUTH AMBOY's NJCL electric-to-diesel
# transition, RARITAN where RVL electrification ends) were left as name-only
# TODOs earlier in this same session, since determining their 2-character
# codes needed either live API access (quota-exhausted all day) or a
# web-fetch tool (unavailable to that session). A later pass in this same
# session had both: cross-referenced chexedy/whereisnjtransit's station
# table (no LICENSE file, so only the factual code->name pairs were used,
# not any of that repo's file/code copied wholesale) and added the four
# codes directly to TRACK_ASSIGNMENT_STATIONS above, flagged UNVERIFIED --
# still not empirically confirmed against the live API, just no longer
# blocked on "codes completely unknown."


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
