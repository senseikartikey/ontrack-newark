"""
Feature engineering for the v2 delay-risk model. Builds the feature set the
project plan specified: line, direction, scheduled hour, day-of-week,
precipitation, temperature, wind, active alert count, recent upstream (same-line)
delay.
"""
import numpy as np
import pandas as pd
from sqlalchemy import select

from models import ServiceAlert, TripUpdate, WeatherHourly

RECENT_DELAY_WINDOW_MINUTES = 60

FEATURE_COLUMNS = [
    "line",
    "direction",
    "hour_of_day",
    "day_of_week",
    "temperature_f",
    "wind_speed_mph",
    "precipitation_probability_pct",
    "active_alerts_for_line",
    "recent_avg_delay_same_line",
]
TARGET_COLUMN = "delay_seconds"


def _load_raw_trip_updates(session) -> pd.DataFrame:
    rows = session.execute(
        select(
            TripUpdate.trip_id,
            TripUpdate.line,
            TripUpdate.direction,
            TripUpdate.scheduled_time,
            TripUpdate.collected_at,
            TripUpdate.delay_seconds,
        ).where(TripUpdate.delay_seconds.is_not(None))
    ).all()
    return pd.DataFrame(
        rows,
        columns=["trip_id", "line", "direction", "scheduled_time", "collected_at", "delay_seconds"],
    )


def _dedupe_one_per_trip_per_day(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (trip_id, calendar day) -- the latest reading -- matching the
    same dedup logic the backend's /scorecard endpoint uses, so a trip polled every
    5 minutes doesn't become many near-duplicate training examples."""
    df = df.copy()
    df["trip_date"] = df["scheduled_time"].dt.date
    df = df.sort_values("collected_at")
    return df.groupby(["trip_id", "trip_date"], as_index=False).last()


def _add_recent_line_delay(df: pd.DataFrame) -> pd.DataFrame:
    """For each row, the mean delay_seconds of OTHER same-line rows strictly within
    the preceding RECENT_DELAY_WINDOW_MINUTES -- a same-line "is this line running
    behind right now" signal. Implemented with an explicit per-line scan (not a
    pandas time-rolling window) so it's easy to verify there's no leakage from a
    row into its own feature."""
    df = df.sort_values("collected_at").reset_index(drop=True)
    window = np.timedelta64(RECENT_DELAY_WINDOW_MINUTES, "m")
    result = [np.nan] * len(df)

    for _, group in df.groupby("line"):
        times = group["collected_at"].to_numpy()
        delays = group["delay_seconds"].to_numpy()
        positions = group.index.to_numpy()
        for i, t in enumerate(times):
            mask = (times < t) & (times >= t - window)
            window_vals = delays[mask]
            result[positions[i]] = float(window_vals.mean()) if len(window_vals) else np.nan

    df["recent_avg_delay_same_line"] = result
    return df


def _load_weather(session) -> pd.DataFrame:
    rows = session.execute(
        select(
            WeatherHourly.forecast_time,
            WeatherHourly.temperature_f,
            WeatherHourly.wind_speed_mph,
            WeatherHourly.precipitation_probability_pct,
        )
    ).all()
    return pd.DataFrame(
        rows,
        columns=["forecast_time", "temperature_f", "wind_speed_mph", "precipitation_probability_pct"],
    )


def _join_nearest_weather(df: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    if weather.empty:
        for col in ["temperature_f", "wind_speed_mph", "precipitation_probability_pct"]:
            df[col] = np.nan
        return df

    df = df.sort_values("scheduled_time")
    weather = weather.sort_values("forecast_time")
    return pd.merge_asof(
        df,
        weather,
        left_on="scheduled_time",
        right_on="forecast_time",
        direction="nearest",
        tolerance=pd.Timedelta("90min"),
    )


def _load_alert_counts(session) -> dict[str, int]:
    """Simple proxy: how many currently-stored alerts mention this line. We don't
    track alert expiry (active_to is never set -- see poll_alerts.py), so this
    counts all alerts ever seen for the line, not just ones active at the trip's
    time. A rough "is this line alert-prone" signal, not a precise point-in-time one."""
    rows = session.execute(select(ServiceAlert.line)).all()
    counts: dict[str, int] = {}
    for (line,) in rows:
        if line:
            counts[line] = counts.get(line, 0) + 1
    return counts


def build_training_frame(session) -> pd.DataFrame:
    """Returns a DataFrame with FEATURE_COLUMNS + TARGET_COLUMN, one row per
    (trip, calendar day), or an empty DataFrame if there's no data yet."""
    df = _load_raw_trip_updates(session)
    if df.empty:
        return df

    df = _dedupe_one_per_trip_per_day(df)
    df = _add_recent_line_delay(df)

    weather = _load_weather(session)
    df = _join_nearest_weather(df, weather)

    alert_counts = _load_alert_counts(session)
    df["active_alerts_for_line"] = df["line"].map(alert_counts).fillna(0)

    df["hour_of_day"] = df["scheduled_time"].dt.hour
    df["day_of_week"] = df["scheduled_time"].dt.weekday
    df["direction"] = df["direction"].fillna("Unknown")
    df["line"] = df["line"].astype("category")
    df["direction"] = df["direction"].astype("category")

    return df
