"""
Read-side SQLAlchemy models, mirroring the tables /ingestion writes (see
/ingestion/models.py). Deliberately a separate definition rather than a shared import:
per AGENTS.md, /backend and /ingestion are owned by different agents and only share a
contract (the DB schema), not code. If the schema changes, both files need updating --
that's an explicit ENGINEERING_LOG.md-worthy event, not something to paper over with a
cross-directory import.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TripUpdate(Base):
    __tablename__ = "trip_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[str] = mapped_column(String)
    line: Mapped[str] = mapped_column(String)
    direction: Mapped[str] = mapped_column(String, nullable=True)
    stop_id: Mapped[str] = mapped_column(String)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WeatherHourly(Base):
    __tablename__ = "weather_hourly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    temperature_f: Mapped[float] = mapped_column(Float, nullable=True)
    wind_speed_mph: Mapped[float] = mapped_column(Float, nullable=True)
    precipitation_probability_pct: Mapped[float] = mapped_column(Float, nullable=True)
    short_forecast: Mapped[str] = mapped_column(String, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DelayBaseline(Base):
    """Read-side mirror of /ml/models.py's DelayBaseline -- see that file's docstring
    for the bucketing convention (Python's datetime.weekday(), Monday=0)."""

    __tablename__ = "delay_baseline"

    line: Mapped[str] = mapped_column(String, primary_key=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer, primary_key=True)
    avg_delay_seconds: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MLPrediction(Base):
    """Read-side mirror of /ml/models.py's MLPrediction -- see that file's
    docstring. Only populated once train_model.py's model clears the minimum
    training-data threshold and beats the statistical baseline."""

    __tablename__ = "ml_predictions"

    line: Mapped[str] = mapped_column(String, primary_key=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer, primary_key=True)
    predicted_delay_seconds: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String)
    mae_seconds: Mapped[float] = mapped_column(Float)
    baseline_mae_seconds: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ServiceAlert(Base):
    __tablename__ = "service_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String)
    line: Mapped[str] = mapped_column(String, nullable=True)
    header_text: Mapped[str] = mapped_column(String)
    description_text: Mapped[str] = mapped_column(String, nullable=True)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    active_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Route(Base):
    """Read-side mirror of /ingestion/models.py's Route (static GTFS routes.txt)."""

    __tablename__ = "routes"

    route_id: Mapped[str] = mapped_column(String, primary_key=True)
    short_name: Mapped[str] = mapped_column(String)
    long_name: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String, nullable=True)


class Stop(Base):
    """Read-side mirror of /ingestion/models.py's Stop (static GTFS stops.txt)."""

    __tablename__ = "stops"

    stop_id: Mapped[str] = mapped_column(String, primary_key=True)
    stop_name: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)


class FeedAnomaly(Base):
    """Read-side mirror of /ingestion/models.py's FeedAnomaly -- see that file's
    docstring and /ingestion/reconcile_anomalies.py for the detection logic that
    populates this table. Powers GET /lines/{line}/data-confidence
    (docs/PRD-v2.md Phase 1's "Data-confidence indicator")."""

    __tablename__ = "feed_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[str] = mapped_column(String)
    line: Mapped[str] = mapped_column(String, nullable=True)
    # "vanished_mid_route" | "stale_timestamp"
    anomaly_type: Mapped[str] = mapped_column(String)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str] = mapped_column(String, nullable=True)


class Trip(Base):
    """Read-side mirror of /ingestion/models.py's Trip (static GTFS trips.txt).

    NOTE (see ENGINEERING_LOG.md, 2026-08-01 "on this train" companion-view entry):
    Trip.trip_id is NOT the same identifier space as the live feed's
    TripUpdate.trip_id (which comes from the live API's raw "ID" field). Empirically
    verified: of 69 distinct live trip_ids sampled, 17 happened to also exist as a
    static trip_id, but for every one of those matches the live trip's line
    disagreed with the matched static trip's route -- i.e. the overlap is a
    coincidental collision between two independently-numbered small-integer ID
    spaces, not a real correspondence. Do not join TripUpdate.trip_id to
    Trip.trip_id directly. Use schedule-proximity matching instead (see
    routers/trips.py).
    """

    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(String, primary_key=True)
    route_id: Mapped[str] = mapped_column(String)
    service_id: Mapped[str] = mapped_column(String)
    trip_headsign: Mapped[str] = mapped_column(String, nullable=True)
    direction_id: Mapped[str] = mapped_column(String, nullable=True)


class TrackAssignment(Base):
    """Read-side mirror of /ingestion/models.py's TrackAssignment -- see that file's
    docstring for the full schema story. Populated by /ingestion's
    poll_track_assignments.py from NJT RailData's getTrainSchedule endpoint.

    `station_code` is NJT's own 2-character station code (e.g. "NP" for Newark Penn
    Station) -- a THIRD station-identifier space in this codebase, distinct from both
    TripUpdate.stop_id (this module's live-feed station *name* strings, e.g. "Newark
    Penn Station", used by GET /stations and GET /stations/{name}/board) and the
    static `stops` table's numeric stop_id (used by GET /stations/{stop_id}/transfers).
    None of the three share a key directly. routers/stations.py's board-enrichment join
    bridges station_code to the live-feed name space via config.TRACK_ASSIGNMENT_STATIONS
    (a name-based lookup, not a numeric one) -- see that router's module docstring.

    `train_id` is NJT's getTrainSchedule TRAIN_ID field, which is NOT confirmed to
    correspond to TripUpdate.trip_id (the live vehicle feed's raw "ID" field) --
    unverified due to /ingestion's 10/day RailData token quota being exhausted before
    a same-train cross-check could be done, and this project has already found (see
    Trip's docstring / routers/trips.py) that superficially similar NJT RailData ID
    fields across different endpoints have turned out to be unrelated ID spaces before.
    routers/stations.py's join therefore does NOT attempt a train_id/trip_id match --
    it uses scheduled_time proximity within the same station_code instead, labeled
    honestly as "schedule_proximity" in the response, same convention as
    routers/trips.py's on-this-train companion view.

    `track` is nullable and, for station_code "NY" (New York Penn Station)
    specifically, is expected to be NULL/empty on essentially every row -- NY Penn is
    Amtrak-dispatched, not NJ Transit's own system, and NJT's own official data
    genuinely has no early visibility into its tracks either. That's an honest, real
    finding to surface as-is (a null track), not a bug to route around.

    This is a time series, not one-row-per-train: the same (station_code, train_id,
    scheduled_time) can appear multiple times as its observed track changes or as a
    periodic unchanged-value checkpoint. Callers needing "the current track" should
    take the most recently observed_at row for a given key, same as
    poll_track_assignments.py's own dedup logic does on the write side.
    """

    __tablename__ = "track_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_code: Mapped[str] = mapped_column(String)
    station_name: Mapped[str] = mapped_column(String, nullable=True)
    train_id: Mapped[str] = mapped_column(String)
    line: Mapped[str] = mapped_column(String, nullable=True)
    destination: Mapped[str] = mapped_column(String, nullable=True)
    track: Mapped[str] = mapped_column(String, nullable=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TrackPrediction(Base):
    """Read-side mirror of /ml/models.py's TrackPrediction -- see that file's
    docstring for the full methodology writeup (styled after Clever Commute's
    published approach: group by exact train_id, not just line/time-of-day).
    Written by /ml's compute_track_predictions.py, precomputed and cached same as
    DelayBaseline/MLPrediction -- the backend never recomputes this per-request.

    One row per train_id (not per station/train pair -- only "NY" (New York Penn
    Station) is covered right now). Only written when sample_size clears
    TRACK_MIN_SAMPLES_LOW (3); below that, no row exists at all for a given
    train_id -- an absence here means "insufficient data," not "predicted no
    track," and callers (see routers/stations.py's GET
    /stations/{station_code}/predicted-tracks) must represent that honestly
    rather than treating a missing row as anything else.

    **Currently empty in production** (2026-08-02, see ENGINEERING_LOG.md): zero
    real non-null track observations exist yet for "NY" in track_assignments, so
    compute_track_predictions.py has nothing to compute predictions from. This is
    a confirmed real finding (NY Penn is Amtrak-dispatched; NJT's own official
    data has no early track visibility there either), not a bug -- design and
    verify any consumer of this table for that honest empty reality.
    """

    __tablename__ = "track_predictions"

    train_id: Mapped[str] = mapped_column(String, primary_key=True)
    station_code: Mapped[str] = mapped_column(String)
    predicted_track: Mapped[str] = mapped_column(String)
    confidence: Mapped[str] = mapped_column(String)  # "high" | "medium" | "low"
    sample_size: Mapped[int] = mapped_column(Integer)
    top_track_share: Mapped[float] = mapped_column(Float)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StopTime(Base):
    """Read-side mirror of /ingestion/models.py's StopTime (static GTFS
    stop_times.txt). arrival_time/departure_time are raw "HH:MM:SS" strings
    (can exceed 24:00:00) -- see routers/trips.py for how these get parsed
    into real datetimes."""

    __tablename__ = "stop_times"

    trip_id: Mapped[str] = mapped_column(String, primary_key=True)
    stop_sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    stop_id: Mapped[str] = mapped_column(String)
    arrival_time: Mapped[str] = mapped_column(String, nullable=True)
    departure_time: Mapped[str] = mapped_column(String, nullable=True)
