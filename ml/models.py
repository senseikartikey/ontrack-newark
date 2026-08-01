"""
SQLAlchemy models for /ml. `TripUpdate` is a read-side mirror of
/ingestion/models.py's table (same pattern as /backend/models.py -- see that file's
docstring for why this isn't a shared import across agent-owned directories).
`DelayBaseline` is a table /ml owns and writes to; /backend reads it.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WeatherHourly(Base):
    """Read-side mirror of /ingestion/models.py's WeatherHourly -- used as a
    feature source by features.py."""

    __tablename__ = "weather_hourly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    temperature_f: Mapped[float] = mapped_column(Float, nullable=True)
    wind_speed_mph: Mapped[float] = mapped_column(Float, nullable=True)
    precipitation_probability_pct: Mapped[float] = mapped_column(Float, nullable=True)
    short_forecast: Mapped[str] = mapped_column(String, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ServiceAlert(Base):
    """Read-side mirror of /ingestion/models.py's ServiceAlert -- used as a
    feature source by features.py (active alert count per line)."""

    __tablename__ = "service_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String)
    line: Mapped[str] = mapped_column(String, nullable=True)
    header_text: Mapped[str] = mapped_column(String)
    description_text: Mapped[str] = mapped_column(String, nullable=True)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    active_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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


class DelayBaseline(Base):
    """
    v1 statistical baseline: average observed delay for a (line, hour_of_day,
    day_of_week) bucket. `hour_of_day` is the scheduled_time's local hour (0-23);
    `day_of_week` follows Python's convention (Monday=0 .. Sunday=6).

    Deliberately does not bucket by weather yet, even though the project plan's
    original v1 description included it -- with zero real data so far, a finer
    bucket just means sparser (and less trustworthy) sample sizes. Weather
    buckets are a reasonable fast-follow once there's enough real history that
    the finer grouping still clears MIN_SAMPLES_THRESHOLD.
    """

    __tablename__ = "delay_baseline"

    line: Mapped[str] = mapped_column(String, primary_key=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer, primary_key=True)
    avg_delay_seconds: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MLPrediction(Base):
    """
    v2 model predictions, precomputed per (line, hour_of_day, day_of_week) bucket --
    same bucketing convention as DelayBaseline, same reason (precomputed and cached,
    not computed per-request, so the backend never needs the model itself loaded).

    Only written by train_model.py when the model clears MIN_TRAINING_ROWS AND beats
    the current statistical baseline's MAE on a held-out test set -- see that file.
    `mae_seconds`/`baseline_mae_seconds` are stored so the backend/README can report
    the comparison honestly rather than just asserting the model is better.
    """

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
