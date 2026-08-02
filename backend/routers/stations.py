"""
Station-grouped "live board" endpoint (docs/PRD-v2.md Phase 1: "DepartureVision-style
live board" -- NJ Transit's own app redesign buried the classic station-board view
behind extra navigation; this restores it as a first-class view).

Where routers.lines' GET /{line}/live is single-line ("what's happening on the NEC"),
this module is station-first ("what's coming through Newark Penn, across every line"),
which is how a physical station board actually works.

Station identity here is TripUpdate.stop_id -- the live feed's raw NEXT_STOP station
*name* string (e.g. "Newark Penn Station"), NOT the static GTFS numeric stop_id (e.g.
"107"). The two have no shared key -- see models.py's TripUpdate docstring reference
and ENGINEERING_LOG.md's 2026-08-01 "NJT RailData access approved" entry, Issue 3, for
the full story. Concretely, this means:
  - GET /stations lists distinct station names actually observed in recent
    trip_updates rows for Newark-area lines, NOT the full 231-row static `stops`
    table (most of which is irrelevant to Newark-area lines and isn't safely
    joinable to live data by numeric ID anyway).
  - GET /stations/{station_name}/board matches station_name case-insensitively
    against TripUpdate.stop_id directly -- no join to the static `stops` table is
    attempted.

GET /stations/{stop_id}/transfers (added for PRD-v2 Phase 1's "transfer-aware hub view",
widened statewide in the i-am-not-happy-pure-aurora plan's step 5) deliberately uses the
OTHER identifier space -- the static GTFS numeric stop_id (e.g. "107" for Newark Penn
Station). It answers a different question than /board: not "what's live right now" but
"which lines structurally call at this station, and roughly when do they next run" --
built entirely from the static schedule (StopTime -> Trip -> Route), since that's the
only reliable join path here (the live feed's own trip_id has no reliable join to static
Trip.trip_id either -- see models.py's Trip docstring / routers/trips.py). Every response
is labeled "scheduled" and is not live data. Existence is checked against the full
statewide static `stops` table (231 rows, no line filter) rather than a hardcoded
allowlist -- any real stop_id works, not just the original two Newark hubs.

GET /stations/static?q=<name> (added in the same step) is the statewide station-name
search that makes the above endpoint actually usable for an arbitrary station: since
/stations/{stop_id}/transfers is keyed by the static numeric stop_id (a different
identifier space than this module's other endpoints' live-feed station-name strings --
see above), a rider/frontend has no way to discover that numeric ID for an arbitrary
station without a search. This does a case-insensitive partial match against the static
`stops` table's stop_name and returns {stop_id, stop_name} pairs.

Track enrichment (added 2026-08-02, /ingestion's poll_track_assignments.py +
TrackAssignment table): GET /stations/{station_name}/board's departures now carry
`track`, `track_match_type`, `track_match_time_gap_minutes` when available. This pulls
in a FOURTH station-identifier space -- TrackAssignment.station_code, NJT RailData's
own 2-character code (e.g. "NP") -- see models.py's TrackAssignment docstring for the
full story. The join has two hops, each deliberately approximate and labeled as such:
  1. Name lookup: `station_name` (this endpoint's TripUpdate.stop_id-space input) is
     matched case-insensitively against config.TRACK_ASSIGNMENT_STATIONS's values to
     resolve a station_code. Only the 17 curated stations in that dict resolve; any
     other station (or NY Penn where NJT itself has no visibility -- see that dict's
     comment) simply gets `track: null` on every departure, not an error.
  2. Train match: TrackAssignment.train_id (NJT's getTrainSchedule TRAIN_ID) is NOT
     assumed to correspond to TripUpdate.trip_id (the live vehicle feed's raw "ID"
     field) -- unverified, since /ingestion's RailData token quota was exhausted
     before a same-train cross-check could be run, and this project has already found
     superficially-similar NJT RailData ID fields across different endpoints to be
     unrelated before (see Trip's docstring / routers/trips.py's live-vs-static
     trip_id finding). So this join does NOT attempt train_id equality at all -- it
     matches each departure to the nearest-in-time TrackAssignment row (same
     station_code, closest scheduled_time, within TRACK_MATCH_MAX_GAP_MINUTES) and
     labels the result `"track_match_type": "schedule_proximity"` with a
     `track_match_time_gap_minutes` gap, the same honesty convention
     routers/trips.py's on-this-train companion view already established for its own
     approximate schedule-proximity join. No line-text filter is applied (TrackAssignment
     only stores getTrainSchedule's free-text LINE field, e.g. "Northeast Corrdr" --
     yet another, differently-formatted identifier space, not this codebase's route
     codes), so a departure could in principle match a different line's train if two
     lines happen to share a near-identical scheduled_time at the same station-code --
     flagged as a known limitation, not expected to matter often in practice.

GET /stations/{station_code}/predicted-tracks (added 2026-08-02, /ml's new
compute_track_predictions.py + TrackPrediction table) is a FIFTH endpoint family in
this module, deliberately keyed on the same TrackAssignment.station_code space as the
track-enrichment join above (not a station_name or numeric stop_id). See that
endpoint's own docstring further down for the full source-data and honesty-labeling
story (a top-level `disclaimer` field on every response, same convention as
routers/trips.py's Quiet Commute lookup).
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import (
    LINE_DISPLAY_NAMES,
    PREDICTED_TRACKS_WINDOW_HOURS,
    RAIL_LINES,
    TRACK_ASSIGNMENT_STATIONS,
)
from db import get_db
from models import Route, Stop, TrackAssignment, TrackPrediction, Trip, TripUpdate, StopTime
from routers.lines import ON_TIME_THRESHOLD_SECONDS

router = APIRouter(tags=["stations"])

# Same rationale as routers/trips.py's _NJT_TZ: GTFS static times are local to the
# agency timezone (Eastern), and we need "now" expressed the same way to compute
# "next departure."
_NJT_TZ = ZoneInfo("America/New_York")

# How many upcoming scheduled departures to return per connecting line.
NEXT_DEPARTURES_PER_LINE = 5

# Cap on GET /stations/static's results -- keeps it usable as a type-ahead search
# rather than returning e.g. every "Newark ..." match at once.
STATION_SEARCH_LIMIT = 20

# Matches routers.lines.LIVE_WINDOW_MINUTES so /stations and /stations/{name}/board
# agree with /lines/{line}/live about what counts as "current."
LIVE_WINDOW_MINUTES = 30

# station_name (lowercased) -> NJT's 2-char track_assignments station_code, built once
# from config.TRACK_ASSIGNMENT_STATIONS. See module docstring's "Track enrichment"
# section -- this is a case-insensitive name lookup, not a numeric join, since none of
# this codebase's station-identifier spaces share a key directly.
_STATION_NAME_TO_TRACK_CODE = {
    name.strip().lower(): code for code, name in TRACK_ASSIGNMENT_STATIONS.items()
}

# Maximum minutes between a departure's scheduled_time and a TrackAssignment row's
# scheduled_time for the two to be considered the same train. Loose enough to survive
# NJT re-scheduling a train by a few minutes between the getTrainSchedule poll and the
# live feed's own SCHED_DEP_TIME, tight enough that two genuinely different departures
# at a busy hub (a few minutes apart at peak) won't usually get cross-matched. Since no
# reliable train_id match exists (see module docstring), this is deliberately
# conservative rather than widened to "closest, no matter how far."
TRACK_MATCH_MAX_GAP_MINUTES = 15


def _live_window_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=LIVE_WINDOW_MINUTES)


def _status(delay_seconds: int | None) -> str:
    """Same on-time convention as routers.lines' scorecard, so the board's status
    labels never disagree with /scorecard about what "on time" means."""
    if delay_seconds is None:
        return "unknown"
    return "on_time" if delay_seconds <= ON_TIME_THRESHOLD_SECONDS else "delayed"


def _attach_track_assignments(
    db: Session, station_code: str | None, departures: list[dict]
) -> None:
    """Enriches each departure dict in `departures` (in place) with `track`,
    `track_match_type`, `track_match_time_gap_minutes`. See module docstring's "Track
    enrichment" section for the full two-hop join strategy and its honesty labeling.

    Always sets all three keys (never leaves them absent), defaulting to None -- a
    predictable per-departure shape regardless of match outcome. Stays a safe no-op
    (every departure keeps `track: null`) when `station_code` is None (station isn't
    one of the 17 curated in TRACK_ASSIGNMENT_STATIONS), when `departures` is empty, or
    when track_assignments simply has no row in range for this station (e.g. the table
    is currently empty in production, or the quota-limited poller hasn't covered this
    station/time yet) -- never raises, never fabricates a value.
    """
    for d in departures:
        d["track"] = None
        d["track_match_type"] = None
        d["track_match_time_gap_minutes"] = None

    if station_code is None or not departures:
        return

    window = timedelta(minutes=TRACK_MATCH_MAX_GAP_MINUTES)
    scheduled_times = [d["scheduled_time"] for d in departures]
    lo = min(scheduled_times) - window
    hi = max(scheduled_times) + window

    rows = (
        db.execute(
            select(TrackAssignment)
            .where(
                TrackAssignment.station_code == station_code,
                TrackAssignment.scheduled_time >= lo,
                TrackAssignment.scheduled_time <= hi,
            )
            .order_by(TrackAssignment.observed_at.desc())
        )
        .scalars()
        .all()
    )
    if not rows:
        return

    # Most recent observation per (train_id, scheduled_time) -- rows are already
    # ordered newest-observed_at-first, so the first row seen per key is the latest.
    # Same "latest wins" convention as poll_track_assignments.py's own dedup logic.
    latest_by_key: dict[tuple[str, datetime], TrackAssignment] = {}
    for row in rows:
        key = (row.train_id, row.scheduled_time)
        if key not in latest_by_key:
            latest_by_key[key] = row
    candidates = latest_by_key.values()

    # Nearest-scheduled_time match per departure, within TRACK_MATCH_MAX_GAP_MINUTES --
    # no train_id/trip_id equality check (see module docstring for why not) and no
    # line-text filter (TrackAssignment.line is a differently-formatted, unverified
    # identifier space -- see module docstring).
    for d in departures:
        best = None
        best_gap = None
        for c in candidates:
            gap_minutes = abs((c.scheduled_time - d["scheduled_time"]).total_seconds()) / 60
            if gap_minutes > TRACK_MATCH_MAX_GAP_MINUTES:
                continue
            if best_gap is None or gap_minutes < best_gap:
                best, best_gap = c, gap_minutes
        if best is not None:
            d["track"] = best.track
            d["track_match_type"] = "schedule_proximity"
            d["track_match_time_gap_minutes"] = round(best_gap, 1)


@router.get("/stations")
def list_stations(db: Session = Depends(get_db)):
    """Distinct station names currently seeing traffic on a Newark-area line
    (within the live window) -- derived from live trip_updates, not the full
    static `stops` table. See module docstring for why."""
    cutoff = _live_window_cutoff()
    rows = (
        db.execute(
            select(TripUpdate.stop_id)
            .where(TripUpdate.line.in_(RAIL_LINES), TripUpdate.collected_at >= cutoff)
            .distinct()
            .order_by(TripUpdate.stop_id)
        )
        .scalars()
        .all()
    )
    return {"stations": [s for s in rows if s]}


@router.get("/stations/{station_name}/board")
def get_station_board(station_name: str, db: Session = Depends(get_db)):
    """
    Station-grouped live board: every upcoming departure across all Newark-area
    lines currently seeing traffic at `station_name`, sorted by scheduled_time
    ascending -- the data a physical station board shows ("what's coming, when,
    on time or not"), not filtered to a single line the way /lines/{line}/live is.

    `station_name` is matched case-insensitively against TripUpdate.stop_id (see
    module docstring for why that's a live-feed station name, not a numeric ID).
    URL-encode the name (e.g. "Newark%20Penn%20Station").

    No 404 for an unrecognized/currently-quiet station name: there's no fixed
    station enumeration to validate against (deliberately -- see module
    docstring), so an empty `departures` list is the honest response for "no
    current Newark-area departures at that name within the live window," mirroring
    /lines/{line}/live's same behavior for a live-but-currently-empty line.

    Each departure also carries `track` (nullable), `track_match_type` (nullable --
    `"schedule_proximity"` when a plausible TrackAssignment row was found, else
    `null`), and `track_match_time_gap_minutes` (nullable). See module docstring's
    "Track enrichment" section for the join strategy and honesty labeling; `track`
    stays `null` for stations outside the 17 curated in TRACK_ASSIGNMENT_STATIONS,
    for New York Penn Station (NJT itself has no early track visibility there), and
    whenever track_assignments simply has no matching row yet.
    """
    cutoff = _live_window_cutoff()
    normalized_name = station_name.strip().lower()

    # Most recent reading per trip_id at this station within the live window --
    # same "collapse repeated polls of the same trip" pattern as
    # routers.lines.get_live_status.
    latest_per_trip = (
        select(
            TripUpdate.trip_id,
            func.max(TripUpdate.collected_at).label("latest_collected_at"),
        )
        .where(
            TripUpdate.line.in_(RAIL_LINES),
            func.lower(TripUpdate.stop_id) == normalized_name,
            TripUpdate.collected_at >= cutoff,
        )
        .group_by(TripUpdate.trip_id)
        .subquery()
    )

    rows = (
        db.execute(
            select(TripUpdate)
            .join(
                latest_per_trip,
                (TripUpdate.trip_id == latest_per_trip.c.trip_id)
                & (TripUpdate.collected_at == latest_per_trip.c.latest_collected_at),
            )
            .order_by(TripUpdate.scheduled_time.asc())
        )
        .scalars()
        .all()
    )

    departures = [
        {
            "trip_id": r.trip_id,
            "line": r.line,
            "line_display_name": LINE_DISPLAY_NAMES.get(r.line, r.line),
            "direction": r.direction,
            "scheduled_time": r.scheduled_time,
            "delay_seconds": r.delay_seconds,
            "status": _status(r.delay_seconds),
        }
        for r in rows
    ]

    track_code = _STATION_NAME_TO_TRACK_CODE.get(normalized_name)
    _attach_track_assignments(db, track_code, departures)

    # Use the station name as actually stored (real-feed casing) once we have at
    # least one match, rather than echoing back the caller's possibly-differently
    # -cased input.
    resolved_station_name = rows[0].stop_id if rows else station_name

    return {
        "station": resolved_station_name,
        "as_of": datetime.now(timezone.utc),
        "departures": departures,
    }


def _parse_gtfs_time_to_minutes(value: str | None) -> float | None:
    """Parses a raw GTFS "HH:MM:SS" string (hours can exceed 24 for after-midnight
    service, e.g. "25:41:00" for 1:41am the next calendar day) into minutes-of-day,
    wrapped into [0, 1440) via mod. Same technique as routers/trips.py's
    _parse_gtfs_time + _minutes_of_day, kept local here since this module has no
    other dependency on that one.

    Wrapping into a plain 0-1439 time-of-day is a deliberate simplification: the
    static feed has no loaded calendar.txt/calendar_dates.txt (see routers/trips.py's
    module docstring, "Known limitation"), so there's no way to know which service_id
    actually runs on a given date anyway -- every scheduled time here is already being
    treated as a generic "this is when this line runs at this hub," not tied to a
    specific date. Mod-1440 just makes an after-midnight entry like "25:41:00" compare
    correctly against a same-day "now" as "1:41am", instead of comparing as a raw 1541
    minutes that would never look "coming up soon" relative to a normal daytime clock.
    """
    if not value:
        return None
    parts = value.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = (int(p) for p in parts)
    except ValueError:
        return None
    return (h * 60 + m + s / 60) % 1440


def _minutes_until(now_minutes: float, target_minutes: float) -> float:
    """Forward-only circular distance from now_minutes to target_minutes, both in
    [0, 1440) minutes-of-day -- e.g. now=23:50 (1430), target=00:19 (19) gives 29
    minutes, correctly treating the target as "tonight, coming up soon" rather than
    "1411 minutes ago." This is the after-midnight-safe piece of the "next departure"
    logic (see module docstring)."""
    return (target_minutes - now_minutes) % 1440


def _format_minutes(minutes_of_day: float) -> str:
    """Formats a [0, 1440) minutes-of-day float back into "HH:MM" wall-clock time."""
    total_minutes = int(round(minutes_of_day)) % 1440
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


@router.get("/stations/static")
def search_stations(q: str, db: Session = Depends(get_db)):
    """
    Statewide station-name search over the static `stops` table (231 rows, no line
    filter -- see module docstring). Case-insensitive partial match against
    stop_name, capped at STATION_SEARCH_LIMIT results so this is usable as a
    type-ahead search. This is the lookup that resolves an arbitrary station name to
    the numeric stop_id GET /stations/{stop_id}/transfers needs (that endpoint's
    identifier space has no other statewide discovery path -- see module docstring).

    Returns {"query": q, "stations": [{"stop_id", "stop_name"}, ...]}. An empty
    `stations` list is a valid, honest response for a query with zero matches (not
    a 404 -- there's nothing wrong with the request, the search just found nothing).
    """
    query = q.strip()
    if not query:
        return {"query": q, "stations": []}

    rows = db.execute(
        select(Stop.stop_id, Stop.stop_name)
        .where(Stop.stop_name.ilike(f"%{query}%"))
        .order_by(Stop.stop_name)
        .limit(STATION_SEARCH_LIMIT)
    ).all()

    return {
        "query": q,
        "stations": [{"stop_id": stop_id, "stop_name": stop_name} for stop_id, stop_name in rows],
    }


@router.get("/stations/{stop_id}/transfers")
def get_station_transfers(stop_id: str, db: Session = Depends(get_db)):
    """
    Transfer-aware hub view (PRD-v2 Phase 1, widened statewide in plan step 5): for
    any real station, which lines actually call there, and roughly when each one's
    next few SCHEDULED (static-timetable) departures are. This is not live data --
    see module docstring for why the live feed can't be reliably used for the
    cross-line part of this feature, and RESPONSE["source"] is always
    "static_schedule" as an explicit label.

    `stop_id` is the static GTFS numeric stop_id (e.g. "107"), NOT the live-feed
    station name /stations and /stations/{name}/board use -- see module docstring.
    Existence is checked against the real statewide `stops` table; a 404 is returned
    only for a genuinely unknown stop_id, not a hardcoded allowlist.
    """
    station = db.get(Stop, stop_id)
    if station is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown stop_id: {stop_id}. Use GET /stations/static?q=<name> to "
                "look up a station's stop_id by name."
            ),
        )
    station_name = station.stop_name

    rows = db.execute(
        select(
            Route.short_name,
            StopTime.trip_id,
            StopTime.departure_time,
            StopTime.arrival_time,
            Trip.trip_headsign,
        )
        .select_from(StopTime)
        .join(Trip, Trip.trip_id == StopTime.trip_id)
        .join(Route, Route.route_id == Trip.route_id)
        .where(StopTime.stop_id == stop_id)
    ).all()

    now_local = datetime.now(_NJT_TZ)
    now_minutes = now_local.hour * 60 + now_local.minute + now_local.second / 60

    # Group scheduled departures by line code.
    by_line: dict[str, list[dict]] = {}
    for short_name, trip_id, departure_time, arrival_time, headsign in rows:
        raw_time = departure_time or arrival_time
        minutes = _parse_gtfs_time_to_minutes(raw_time)
        if minutes is None:
            continue
        by_line.setdefault(short_name, []).append(
            {
                "minutes_of_day": minutes,
                "raw_time": raw_time,
                "headsign": headsign,
                "minutes_until": _minutes_until(now_minutes, minutes),
            }
        )

    lines = []
    for short_name, entries in sorted(by_line.items()):
        # Dedupe identical (time, headsign) pairs -- the same scheduled run can appear
        # more than once if multiple service_ids (e.g. weekday/weekend variants) share
        # an identical stop_time, and we have no calendar.txt loaded to tell them apart
        # (see _parse_gtfs_time_to_minutes' docstring).
        seen = set()
        deduped = []
        for entry in entries:
            key = (round(entry["minutes_of_day"], 2), entry["headsign"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)

        deduped.sort(key=lambda e: e["minutes_until"])
        upcoming = deduped[:NEXT_DEPARTURES_PER_LINE]

        lines.append(
            {
                "line": short_name,
                "line_display_name": LINE_DISPLAY_NAMES.get(short_name, short_name),
                "distinct_scheduled_times": len(deduped),
                "next_departures": [
                    {
                        "scheduled_time_of_day": _format_minutes(e["minutes_of_day"]),
                        "headsign": e["headsign"],
                        "minutes_until": round(e["minutes_until"], 1),
                    }
                    for e in upcoming
                ],
            }
        )

    return {
        "stop_id": stop_id,
        "station_name": station_name,
        "source": "static_schedule",
        "note": (
            "Scheduled (static-timetable) departures, not live predictions. No "
            "calendar.txt/calendar_dates.txt is loaded yet, so these times reflect "
            "the general daily timetable across all service_ids rather than a "
            "specific date's actual (e.g. weekday-vs-weekend) service pattern."
        ),
        "as_of": datetime.now(timezone.utc),
        "lines": lines,
    }


# ---------------------------------------------------------------------------
# Predicted tracks (2026-08-02): a historical-pattern per-train track prediction
# for New York Penn Station, precomputed by /ml's compute_track_predictions.py into
# `track_predictions`. See that table's docstring (models.py's TrackPrediction) and
# /ml's compute_track_predictions.py module docstring for the full methodology and
# why NY Penn specifically has no official early track visibility at all.

# Small backward grace window for GET /stations/{station_code}/predicted-tracks -- a
# train scheduled a few minutes ago is very likely still boarding, not meaningfully
# "in the past" for a rider checking this endpoint. Same order of magnitude as
# TRACK_MATCH_MAX_GAP_MINUTES above, kept as a separate constant since it answers a
# different question (how far back to still call a departure "upcoming" vs. how wide
# a schedule-proximity match window is).
PREDICTED_TRACKS_PAST_GRACE_MINUTES = 5

# Same "confident-sounding feature, honest about actual certainty" convention as
# routers/trips.py's QUIET_COMMUTE_DISCLAIMER -- included on every response, not
# just when a real prediction is present, since even a real TrackPrediction row is
# a historical-pattern estimate, never a guarantee.
PREDICTED_TRACKS_DISCLAIMER = (
    "Historical-pattern estimate only -- not an official NJ Transit or Amtrak source. "
    "New York Penn Station is Amtrak-dispatched, and neither NJT's own systems nor "
    "Amtrak publish early track assignments for it; every real NJT RailData "
    "observation captured for this station so far has come back with a null track "
    "(see ENGINEERING_LOG.md, 2026-08-02). When a prediction is present below, it is "
    "inferred from how often this specific train has historically used a given track "
    "(styled after third-party tools like Clever Commute / nypenn.live), not from any "
    "live or official schedule data -- always confirm with posted station signage "
    "before heading to a platform."
)


@router.get("/stations/{station_code}/predicted-tracks")
def get_predicted_tracks(station_code: str, db: Session = Depends(get_db)):
    """
    Upcoming departures at a station, keyed by NJT RailData's own 2-character
    station_code (e.g. "NY" for New York Penn Station -- see models.py's
    TrackAssignment docstring for why this is a fourth, distinct station-identifier
    space from this module's other endpoints), enriched with a precomputed
    per-train track prediction when one exists.

    Built for New York Penn Station specifically: NY Penn is Amtrak-dispatched, so
    neither NJT's own official data nor this project's live feed has any early
    track visibility there -- this endpoint answers "which track will train X
    probably use" the same way third-party tools like Clever Commute/nypenn.live
    do, from historical pattern, never from any live or official source. That
    honesty is also why every response always carries a top-level `disclaimer`
    field (PREDICTED_TRACKS_DISCLAIMER) -- same convention as routers/trips.py's
    Quiet Commute lookup.

    Source data, two tables:
      - `track_assignments` (/ingestion's poll_track_assignments.py, logging NJT
        RailData's getTrainSchedule) supplies the upcoming-departures list itself:
        every distinct (train_id, scheduled_time) on file for `station_code` with
        scheduled_time within [now - grace, now + PREDICTED_TRACKS_WINDOW_HOURS].
        This is a time series (see TrackAssignment's docstring) -- only the most
        recently observed row per (train_id, scheduled_time) key is used, same
        "latest wins" convention as this module's board-enrichment join above.
      - `track_predictions` (/ml's compute_track_predictions.py) supplies the
        prediction itself, joined on train_id. **Currently empty in production**
        (zero real non-null track observations exist yet for "NY" -- a confirmed
        real finding, not a bug; see TrackPrediction's docstring) -- so right now
        every departure honestly gets `confidence: "insufficient_data"`, never a
        fabricated track.

    No 404 for an unrecognized/quiet station_code: same reasoning as
    GET /stations/{station_name}/board -- there's no fixed enumeration to validate
    against here either (`TrackAssignment.station_code` is whatever NJT RailData
    happens to have been polled for), so an empty `departures` list is the honest
    response for "nothing on file for that code in the window," not an error.
    `station_code` is matched case-insensitively (normalized to uppercase, matching
    how track_assignments/TRACK_ASSIGNMENT_STATIONS actually store NJT's codes).
    """
    normalized_code = station_code.strip().upper()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=PREDICTED_TRACKS_PAST_GRACE_MINUTES)
    window_end = now + timedelta(hours=PREDICTED_TRACKS_WINDOW_HOURS)

    rows = (
        db.execute(
            select(TrackAssignment)
            .where(
                TrackAssignment.station_code == normalized_code,
                TrackAssignment.scheduled_time >= window_start,
                TrackAssignment.scheduled_time <= window_end,
            )
            .order_by(TrackAssignment.observed_at.desc())
        )
        .scalars()
        .all()
    )

    # Most recent observation per (train_id, scheduled_time) -- rows are already
    # ordered newest-observed_at-first, so the first row seen per key is the latest.
    # Same convention as _attach_track_assignments above.
    latest_by_key: dict[tuple[str, datetime], TrackAssignment] = {}
    for row in rows:
        key = (row.train_id, row.scheduled_time)
        if key not in latest_by_key:
            latest_by_key[key] = row
    departures = sorted(latest_by_key.values(), key=lambda r: r.scheduled_time)

    predictions_by_train: dict[str, TrackPrediction] = {}
    train_ids = {d.train_id for d in departures}
    if train_ids:
        pred_rows = (
            db.execute(select(TrackPrediction).where(TrackPrediction.train_id.in_(train_ids)))
            .scalars()
            .all()
        )
        predictions_by_train = {p.train_id: p for p in pred_rows}

    results = []
    for d in departures:
        prediction = predictions_by_train.get(d.train_id)
        if prediction is not None:
            results.append(
                {
                    "train_id": d.train_id,
                    "line": d.line,
                    "destination": d.destination,
                    "scheduled_time": d.scheduled_time,
                    "predicted_track": prediction.predicted_track,
                    "confidence": prediction.confidence,
                    "sample_size": prediction.sample_size,
                    "top_track_share": prediction.top_track_share,
                }
            )
        else:
            # No TrackPrediction row on file for this train_id -- honestly
            # "insufficient_data", never a fabricated track. See module docstring
            # and TrackPrediction's own docstring for why this is the expected,
            # confirmed-real state for every "NY" train right now.
            results.append(
                {
                    "train_id": d.train_id,
                    "line": d.line,
                    "destination": d.destination,
                    "scheduled_time": d.scheduled_time,
                    "predicted_track": None,
                    "confidence": "insufficient_data",
                    "sample_size": 0,
                    "top_track_share": None,
                }
            )

    return {
        "station_code": normalized_code,
        "as_of": now,
        "window_hours": PREDICTED_TRACKS_WINDOW_HOURS,
        "disclaimer": PREDICTED_TRACKS_DISCLAIMER,
        "departures": results,
    }
