"""
"On this train" companion view (docs/PRD-v2.md Phase 1): ordered upcoming stops for
a currently-active trip, so a rider mid-trip can see what's coming next -- something
NJ Transit's own redesigned app regressed on.

Join-strategy note (see ENGINEERING_LOG.md's 2026-08-01 "on this train" companion-view
entry, and models.py's Trip docstring): the live feed's TripUpdate.trip_id and static
GTFS's Trip.trip_id are NOT the same identifier space. Empirically verified against
real production data: of 69 distinct live trip_ids sampled, 17 coincidentally also
existed as a static trip_id, but 0 of the resulting 32 matched (trip_id, reading) rows
agreed on which line/route the trip actually belonged to -- confirming the overlap is
a chance collision between two independently-numbered small-integer ID spaces, not a
real correspondence. This is the same category of mismatch already hit with stop_id
(see the RailData ENGINEERING_LOG entry's "Issue 3").

Falls back to schedule-proximity matching instead: given a live trip's line +
direction + scheduled_time, find the static Trip on that route (matched via
Route.short_name, filtered by direction when the live "Eastbound"/"Westbound" value
maps cleanly to a static direction_id -- see _DIRECTION_TO_STATIC_ID) whose own first
scheduled stop is closest in time-of-day, and use that trip's stop sequence as a
best-effort stand-in. This is never presented as ground truth: every response is
labeled `"match_type": "schedule_proximity"` and includes `match_time_gap_minutes`
(the actual time-of-day gap between the live trip's own scheduled time and the
matched static trip's first-stop time) so a caller can judge match quality itself.

Per-stop `estimated_arrival` values are the matched trip's static schedule with the
live trip's current known `delay_seconds` applied as a uniform offset to every
remaining stop -- NOT a per-stop live reading (the live feed only ever reports one
current "next stop" per trip, not a full position history), so this is clearly an
estimate carried forward from the last known delay, not ground truth either.

Known limitation: no calendar.txt/calendar_dates.txt is loaded (ingestion only loads
trips.txt/stop_times.txt so far), so candidate matching can't filter by which
service_id actually runs today -- a candidate trip that only runs on a different day
of the week could theoretically be selected if its schedule happens to be the closest
time-of-day match. Not expected to matter much in practice (Newark-area weekday/
weekend schedules are broadly similar in structure), but worth knowing if a match
ever looks structurally off.
"""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_db
from models import Route, Stop, StopTime, Trip, TripUpdate

router = APIRouter(prefix="/trips", tags=["trips"])

# GTFS static times are local to the agency timezone; so are the live feed's
# timestamps (see ingestion/poll_gtfs_rt.py's _NJT_TZ). Needed to convert between the
# two consistently.
_NJT_TZ = ZoneInfo("America/New_York")

# Empirically verified against real trips.txt data (see models.py's Trip docstring):
# direction_id "0" trips head toward New York Penn/Hoboken (the live feed's
# "Eastbound"); direction_id "1" trips head away from NYC ("Westbound"). Checked
# across NEC, MNE, NJCL, RARV, and BNTN's trip_headsign values -- consistent in every
# case sampled.
_DIRECTION_TO_STATIC_ID = {"Eastbound": "0", "Westbound": "1"}


def _parse_gtfs_time(value: str | None) -> timedelta | None:
    """Parses a raw GTFS "HH:MM:SS" string (hours can exceed 24 for after-midnight
    service) into a timedelta offset from midnight of the service date."""
    if not value:
        return None
    parts = value.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = (int(p) for p in parts)
    except ValueError:
        return None
    return timedelta(hours=h, minutes=m, seconds=s)


def _minutes_of_day(offset: timedelta) -> float:
    return (offset.total_seconds() / 60) % 1440


def _circular_diff_minutes(a: float, b: float) -> float:
    """Time-of-day distance that correctly handles midnight wraparound (e.g. 23:55
    and 00:05 are 10 minutes apart, not ~1430)."""
    diff = abs(a - b)
    return min(diff, 1440 - diff)


@router.get("/{trip_id}/upcoming-stops")
def get_upcoming_stops(trip_id: str, db: Session = Depends(get_db)):
    """Ordered list of a live trip's remaining stops with estimated arrival times.
    See module docstring for the schedule-proximity join strategy and its caveats."""
    # 1. Most recent live reading for this trip, across any stop_id it's reported at
    # (mirrors routers.lines.get_live_status's "collapse repeated polls" pattern, but
    # for a single trip rather than a whole line).
    latest = (
        db.execute(
            select(TripUpdate)
            .where(TripUpdate.trip_id == trip_id)
            .order_by(TripUpdate.collected_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )

    if latest is None:
        raise HTTPException(status_code=404, detail=f"No live data found for trip_id {trip_id}")

    # 2. Resolve the static route for this trip's line.
    route = db.execute(select(Route).where(Route.short_name == latest.line)).scalars().first()
    if route is None:
        return {
            "trip_id": trip_id,
            "line": latest.line,
            "status": "insufficient_data",
            "message": f"No static schedule data loaded for line {latest.line}.",
        }

    # 3. Candidate static trips on that route, filtered by direction when we can map
    # it. Relax the direction filter (rather than fail) if it excludes everything --
    # a same-line, unfiltered-direction match is still more useful than none.
    direction_static_id = _DIRECTION_TO_STATIC_ID.get(latest.direction or "")
    candidates_stmt = select(Trip.trip_id).where(Trip.route_id == route.route_id)
    if direction_static_id is not None:
        candidates_stmt = candidates_stmt.where(Trip.direction_id == direction_static_id)
    candidate_ids = db.execute(candidates_stmt).scalars().all()

    if not candidate_ids and direction_static_id is not None:
        candidate_ids = (
            db.execute(select(Trip.trip_id).where(Trip.route_id == route.route_id)).scalars().all()
        )

    if not candidate_ids:
        return {
            "trip_id": trip_id,
            "line": latest.line,
            "status": "insufficient_data",
            "message": f"No static trips found on route {route.route_id} ({latest.line}).",
        }

    # 4. For each candidate, find its first scheduled stop (min stop_sequence).
    first_seq_subq = (
        select(StopTime.trip_id, func.min(StopTime.stop_sequence).label("min_seq"))
        .where(StopTime.trip_id.in_(candidate_ids))
        .group_by(StopTime.trip_id)
        .subquery()
    )
    first_stops = db.execute(
        select(StopTime.trip_id, StopTime.departure_time, StopTime.arrival_time).join(
            first_seq_subq,
            (StopTime.trip_id == first_seq_subq.c.trip_id)
            & (StopTime.stop_sequence == first_seq_subq.c.min_seq),
        )
    ).all()

    # 5. Pick the candidate whose first-stop time-of-day is closest to the live
    # trip's own scheduled_time (converted to Eastern local time-of-day).
    local_scheduled = latest.scheduled_time.astimezone(_NJT_TZ)
    live_minutes = local_scheduled.hour * 60 + local_scheduled.minute + local_scheduled.second / 60

    best_trip_id = None
    best_diff = None
    for cand_trip_id, departure_time, arrival_time in first_stops:
        offset = _parse_gtfs_time(departure_time) or _parse_gtfs_time(arrival_time)
        if offset is None:
            continue
        diff = _circular_diff_minutes(live_minutes, _minutes_of_day(offset))
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_trip_id = cand_trip_id

    if best_trip_id is None:
        return {
            "trip_id": trip_id,
            "line": latest.line,
            "status": "insufficient_data",
            "message": "No static trips on this route have usable scheduled stop times.",
        }

    # 6. Ordered stop sequence for the matched static trip, joined to station names.
    stop_rows = db.execute(
        select(StopTime, Stop.stop_name)
        .join(Stop, Stop.stop_id == StopTime.stop_id, isouter=True)
        .where(StopTime.trip_id == best_trip_id)
        .order_by(StopTime.stop_sequence.asc())
    ).all()

    service_date = local_scheduled.date()
    midnight = datetime.combine(service_date, time(0, 0, 0), tzinfo=_NJT_TZ)
    delay_seconds = latest.delay_seconds or 0
    now = datetime.now(timezone.utc)

    stops = []
    for stop_time, stop_name in stop_rows:
        raw_offset = _parse_gtfs_time(stop_time.arrival_time) or _parse_gtfs_time(stop_time.departure_time)
        if raw_offset is None:
            estimated_arrival = None
            passed = None
        else:
            scheduled_dt = midnight + raw_offset
            estimated_arrival = scheduled_dt + timedelta(seconds=delay_seconds)
            passed = estimated_arrival < now

        stops.append(
            {
                "stop_sequence": stop_time.stop_sequence,
                "stop_id": stop_time.stop_id,
                "station_name": stop_name,
                "scheduled_time": stop_time.arrival_time or stop_time.departure_time,
                "estimated_arrival": estimated_arrival,
                "passed": passed,
            }
        )

    return {
        "trip_id": trip_id,
        "line": latest.line,
        "direction": latest.direction,
        "status": "ok",
        "match_type": "schedule_proximity",
        "matched_static_trip_id": best_trip_id,
        "match_time_gap_minutes": round(best_diff, 1),
        "current_delay_seconds": latest.delay_seconds,
        "as_of": now,
        "stops": stops,
    }


# ---------------------------------------------------------------------------
# Quiet Commute car lookup (docs/PRD-v2.md Phase 1's "Quiet Commute car lookup").
#
# NJ Transit's own press release describes the program as expanded to NEC peak-hour
# trains serving Newark and NY Penn, but gives no machine-readable list of which
# specific trains carry a quiet car -- and this project has already verified (see
# this module's docstring above, and models.py's Trip docstring) that neither the
# live feed's trip_id nor static GTFS's trip_id corresponds to any published NJT
# train-number scheme. So this is deliberately NOT a lookup keyed on an assumed
# train-number match: it's a best-effort rule applied only to signals this project
# can actually verify from real data -- the line (must be NEC) and weekday
# peak-hour timing + direction.
#
# Direction: reuses `TripUpdate.direction` ("Eastbound"/"Westbound"), the same live
# field already used above for schedule-proximity matching. That Eastbound=inbound
# (toward Newark/NY Penn) / Westbound=outbound mapping isn't assumed here -- it's the
# one this module's docstring says was empirically checked against static GTFS's own
# `direction_id`/`trip_headsign` across every Newark-area line (see
# _DIRECTION_TO_STATIC_ID above). Reusing it is preferable to a fresh static `Trip`
# join keyed on this endpoint's `trip_id` path param, which would be a live-trip_id
# used as if it were a static trip_id -- exactly the unverified join this project has
# already confirmed is wrong.
#
# Peak windows: weekday AM 6:00-10:00 (inbound to Newark/NY Penn) and PM 16:00-20:00
# (outbound from Newark/NY Penn). This is the commonly understood NJT peak-hour
# definition (AM rush into the city, PM rush back out) -- not sourced from a precise
# NJT machine-readable spec (none exists for this program), so treat these windows as
# a reasonable convention, not an official cutoff.
_AM_PEAK_START = time(6, 0)
_AM_PEAK_END = time(10, 0)
_PM_PEAK_START = time(16, 0)
_PM_PEAK_END = time(20, 0)

QUIET_COMMUTE_DISCLAIMER = (
    "Best-effort estimate only -- not an official NJ Transit source. NJ Transit's "
    "public materials describe Quiet Commute cars as running on Northeast Corridor "
    "peak-hour trains into Newark and New York Penn Station, but publish no "
    "machine-readable list of which specific trains carry one. This project has no "
    "way to verify a train's actual consist (which physical car is the quiet car, or "
    "whether one is present at all) from any data source it has access to. This is a "
    "rule-of-thumb inference from the trip's line and weekday peak-hour timing/"
    "direction, not a guarantee -- always confirm with onboard signage."
)


def _quiet_commute_assessment(line: str, direction: str | None, local_scheduled: datetime) -> dict:
    """Best-effort rule: NEC + weekday + the matching peak-direction window. See the
    block comment above _AM_PEAK_START for the full reasoning and caveats."""
    is_nec = line == "NEC"
    is_weekday = local_scheduled.weekday() < 5  # datetime.weekday(): Monday=0 ... Sunday=6
    local_time = local_scheduled.time()
    in_am_window = _AM_PEAK_START <= local_time < _AM_PEAK_END
    in_pm_window = _PM_PEAK_START <= local_time < _PM_PEAK_END
    time_str = local_scheduled.strftime("%H:%M")
    day_str = local_scheduled.strftime("%A")

    if not is_nec:
        return {
            "likely_quiet_commute": False,
            "reasoning": (
                f"Line is {line}, not Northeast Corridor (NEC). NJ Transit's Quiet "
                "Commute program is NEC-specific."
            ),
        }

    if not is_weekday:
        return {
            "likely_quiet_commute": False,
            "reasoning": (
                f"NEC, but scheduled for {day_str}, a weekend day. Quiet Commute cars "
                "run on weekday peak-hour trains only."
            ),
        }

    # Eastbound = inbound toward Newark/NY Penn, Westbound = outbound -- see the
    # block comment above _AM_PEAK_START for where this mapping was verified.
    if direction == "Eastbound":
        if in_am_window:
            return {
                "likely_quiet_commute": True,
                "reasoning": (
                    f"NEC, {day_str} {time_str} local, inbound toward Newark/NY Penn "
                    "during the AM peak window (6:00-10:00) -- matches the profile of "
                    "NJ Transit's expanded Quiet Commute program."
                ),
            }
        return {
            "likely_quiet_commute": False,
            "reasoning": (
                f"NEC, {day_str} {time_str} local, inbound toward Newark/NY Penn, but "
                "outside the AM peak window (6:00-10:00) this project uses for the "
                "inbound peak direction."
            ),
        }

    if direction == "Westbound":
        if in_pm_window:
            return {
                "likely_quiet_commute": True,
                "reasoning": (
                    f"NEC, {day_str} {time_str} local, outbound from Newark/NY Penn "
                    "during the PM peak window (16:00-20:00) -- matches the profile of "
                    "NJ Transit's expanded Quiet Commute program."
                ),
            }
        return {
            "likely_quiet_commute": False,
            "reasoning": (
                f"NEC, {day_str} {time_str} local, outbound from Newark/NY Penn, but "
                "outside the PM peak window (16:00-20:00) this project uses for the "
                "outbound peak direction."
            ),
        }

    # Direction missing/unrecognized -- fall back to time-of-day only, and say so
    # plainly rather than silently guessing a direction.
    if in_am_window or in_pm_window:
        window = "AM (6:00-10:00)" if in_am_window else "PM (16:00-20:00)"
        return {
            "likely_quiet_commute": True,
            "reasoning": (
                f"NEC, {day_str} {time_str} local, within the {window} peak window, but "
                "this trip's direction could not be determined from the live feed, so "
                "the inbound/outbound peak-direction pattern NJ Transit describes could "
                "not be checked -- treated as a likely peak trip on a best-effort basis."
            ),
        }
    return {
        "likely_quiet_commute": False,
        "reasoning": (
            f"NEC, {day_str} {time_str} local, outside both the AM (6:00-10:00) and PM "
            "(16:00-20:00) peak windows this project uses."
        ),
    }


@router.get("/{trip_id}/quiet-commute")
def get_quiet_commute_likelihood(trip_id: str, db: Session = Depends(get_db)):
    """Best-effort Quiet Commute car lookup (docs/PRD-v2.md Phase 1). See the block
    comment above _AM_PEAK_START for why this is a rule-based inference rather than a
    lookup against a specific train, and QUIET_COMMUTE_DISCLAIMER for the exact
    rider-facing caveat included in every response. 404s under the same condition as
    /upcoming-stops: no trip_updates row at all for this trip_id."""
    latest = (
        db.execute(
            select(TripUpdate)
            .where(TripUpdate.trip_id == trip_id)
            .order_by(TripUpdate.collected_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No live data found for trip_id {trip_id}")

    local_scheduled = latest.scheduled_time.astimezone(_NJT_TZ)
    assessment = _quiet_commute_assessment(latest.line, latest.direction, local_scheduled)

    return {
        "trip_id": trip_id,
        "line": latest.line,
        "direction": latest.direction,
        "scheduled_time": latest.scheduled_time,
        "likely_quiet_commute": assessment["likely_quiet_commute"],
        "confidence": "best_effort",
        "reasoning": assessment["reasoning"],
        "disclaimer": QUIET_COMMUTE_DISCLAIMER,
    }
