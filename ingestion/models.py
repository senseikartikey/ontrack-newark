"""SQLAlchemy models for the ingestion layer's Postgres tables."""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
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
