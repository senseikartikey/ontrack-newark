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
