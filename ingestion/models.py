"""SQLAlchemy models for the ingestion layer's Postgres tables."""
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TripUpdate(Base):
    """One observed delay reading for a trip at a stop, from GTFS-RT trip updates."""

    __tablename__ = "trip_updates"
    __table_args__ = (
        UniqueConstraint("trip_id", "stop_id", "collected_at", name="uq_trip_stop_collected"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[str] = mapped_column(String, index=True)
    line: Mapped[str] = mapped_column(String, index=True)
    direction: Mapped[str] = mapped_column(String, nullable=True)
    stop_id: Mapped[str] = mapped_column(String, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class WeatherHourly(Base):
    """Hourly weather snapshot for the Newark area, from NWS."""

    __tablename__ = "weather_hourly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), unique=True, index=True)
    temperature_f: Mapped[float] = mapped_column(Float, nullable=True)
    wind_speed_mph: Mapped[float] = mapped_column(Float, nullable=True)
    precipitation_probability_pct: Mapped[float] = mapped_column(Float, nullable=True)
    short_forecast: Mapped[str] = mapped_column(String, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Route(Base):
    """Static reference data from routes.txt in NJ Transit's public GTFS feed."""

    __tablename__ = "routes"

    route_id: Mapped[str] = mapped_column(String, primary_key=True)
    short_name: Mapped[str] = mapped_column(String, index=True)
    long_name: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String, nullable=True)


class Stop(Base):
    """Static reference data from stops.txt in NJ Transit's public GTFS feed."""

    __tablename__ = "stops"

    stop_id: Mapped[str] = mapped_column(String, primary_key=True)
    stop_name: Mapped[str] = mapped_column(String, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)


class ServiceAlert(Base):
    """An active NJ Transit rail service alert."""

    __tablename__ = "service_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    line: Mapped[str] = mapped_column(String, nullable=True, index=True)
    header_text: Mapped[str] = mapped_column(String)
    description_text: Mapped[str] = mapped_column(String, nullable=True)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    active_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Trip(Base):
    """Static reference data from trips.txt in NJ Transit's public GTFS feed.

    One row per scheduled trip -- links a route to its ordered stop sequence
    (via StopTime.trip_id) and records which direction it runs.
    """

    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(String, primary_key=True)
    route_id: Mapped[str] = mapped_column(String, index=True)
    service_id: Mapped[str] = mapped_column(String, index=True)
    trip_headsign: Mapped[str] = mapped_column(String, nullable=True)
    direction_id: Mapped[str] = mapped_column(String, nullable=True)


class FeedAnomaly(Base):
    """A detected unreliability pattern in the live GTFS-RT feed itself -- e.g. a
    trip that vanished mid-route, or a reading that looks stale/cached. Powers
    the data-confidence indicator (see docs/PRD-v2.md Phase 1). Additive table;
    doesn't touch trip_updates' existing schema/consumers. See
    reconcile_anomalies.py for the detection logic that populates this.
    """

    __tablename__ = "feed_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[str] = mapped_column(String, index=True)
    line: Mapped[str] = mapped_column(String, nullable=True, index=True)
    # "vanished_mid_route" | "stale_timestamp"
    anomaly_type: Mapped[str] = mapped_column(String, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    detail: Mapped[str] = mapped_column(String, nullable=True)


class StopTime(Base):
    """Static reference data from stop_times.txt in NJ Transit's public GTFS feed.

    One row per (trip, stop) -- ordered by stop_sequence within a trip_id gives
    the trip's ordered list of stops. arrival_time/departure_time are stored as
    the raw GTFS "HH:MM:SS" string (can exceed 24:00:00 for after-midnight
    service) since there's no date context here to parse them into a datetime.
    """

    __tablename__ = "stop_times"

    trip_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    stop_sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    stop_id: Mapped[str] = mapped_column(String, index=True)
    arrival_time: Mapped[str] = mapped_column(String, nullable=True)
    departure_time: Mapped[str] = mapped_column(String, nullable=True)


class NjtTokenCache(Base):
    """Persists the NJT RailData bearer token across separate process invocations.

    Real, live-discovered 2026-08-02 (see ENGINEERING_LOG.md): NJT RailData enforces
    a very low account-wide daily quota on `getToken` issuance -- a real request
    returned `{"errorMessage":"Daily usage limit:10. Your current daily usage: 11"}`.
    `njt_client.py`'s `_Token` caching only ever lived in one Python process's
    memory, which is fine *within* a single script run but useless across runs --
    every scheduled GitHub Actions poll invokes each poller script (poll_gtfs_rt.py,
    poll_alerts.py, and now poll_track_assignments.py) as a brand-new process every
    5 minutes, so without this table each invocation minted its own fresh token
    via getToken rather than reusing one across the ~25-minute assumed token TTL --
    multiplying real token requests far beyond what NJT's account actually allows
    in a day. njt_client.py now checks this table before calling getToken, and
    writes the freshly issued token back here after a real fetch, so a single
    token is shared by every poller process until it's genuinely due to expire.

    Single-row table by design (id is always 1) -- there is only ever one current
    token worth sharing account-wide.
    """

    __tablename__ = "njt_token_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TrackAssignment(Base):
    """A single observed track-assignment reading for one scheduled train at one
    station, from NJT RailData's getTrainSchedule endpoint (see njt_client.py's
    `get_train_schedule` and poll_track_assignments.py). Uses NJT's own 2-character
    station code (e.g. "NP" for Newark Penn Station) -- a THIRD station-identifier
    space in this codebase, distinct from both TripUpdate.stop_id's live-feed
    station *name* strings and the static `stops` table's numeric stop_id. See
    poll_track_assignments.py's module docstring and ENGINEERING_LOG.md's
    2026-08-02 entry for the full story; don't conflate any of the three.

    This is a genuine time-series log, not an upsert-by-train keyed table: the
    same scheduled train (station_code, train_id, scheduled_time) is expected to
    be observed across many poll cycles as its departure approaches, and the
    whole point is to see whether/when its `track` value changes (e.g. empty ->
    populated, or one track reassigned to another) -- overwriting prior
    observations would destroy exactly the signal this table exists to capture.
    poll_track_assignments.py only inserts a new row when the observed track
    differs from the most recent one on file for that (station_code, train_id,
    scheduled_time) triple, or enough time has passed since the last observation
    -- see that module's dedup logic -- so this table grows with real track
    *changes* over time, not one row per poll per train.

    `track` is nullable and, for station_code "NY" (New York Penn Station)
    specifically, is expected to be NULL/empty on essentially every row -- NY
    Penn is Amtrak-dispatched, not NJ Transit's own system, and NJT's own official
    data genuinely has no early visibility into its tracks either. That is an
    honest, real finding this table is designed to keep proving over time, not a
    bug to route around.
    """

    __tablename__ = "track_assignments"
    __table_args__ = (
        Index("ix_track_assignments_lookup", "station_code", "train_id", "scheduled_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_code: Mapped[str] = mapped_column(String, index=True)
    station_name: Mapped[str] = mapped_column(String, nullable=True)
    train_id: Mapped[str] = mapped_column(String, index=True)
    line: Mapped[str] = mapped_column(String, nullable=True)
    destination: Mapped[str] = mapped_column(String, nullable=True)
    track: Mapped[str] = mapped_column(String, nullable=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
