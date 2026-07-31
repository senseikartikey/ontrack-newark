"""
Client for the National Weather Service API (api.weather.gov) — public, no API key
required, just a descriptive User-Agent per NWS policy. Grid coordinates for Newark, NJ
were confirmed live against /points on 2026-07-30 (see config.py).
"""
from __future__ import annotations

import requests

from config import NWS_HOURLY_FORECAST_URL, WEATHER_USER_AGENT


def fetch_hourly_forecast() -> list[dict]:
    """Returns the raw list of hourly forecast periods for the Newark grid point."""
    resp = requests.get(
        NWS_HOURLY_FORECAST_URL,
        headers={"User-Agent": WEATHER_USER_AGENT, "Accept": "application/geo+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["properties"]["periods"]


def parse_period(period: dict) -> dict:
    """Extracts the fields we store from one NWS hourly forecast period."""
    precip = period.get("probabilityOfPrecipitation", {}) or {}
    return {
        "forecast_time": period["startTime"],
        "temperature_f": period.get("temperature"),
        "wind_speed_mph": _parse_wind_speed(period.get("windSpeed")),
        "precipitation_probability_pct": precip.get("value"),
        "short_forecast": period.get("shortForecast"),
    }


def _parse_wind_speed(wind_speed_str: str | None) -> float | None:
    """NWS returns wind speed as a string like '10 mph' or '5 to 10 mph'; take the
    first number as a simple point estimate."""
    if not wind_speed_str:
        return None
    first_token = wind_speed_str.split()[0]
    try:
        return float(first_token)
    except ValueError:
        return None
