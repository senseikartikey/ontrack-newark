"""Entrypoint: fetch the latest NWS hourly forecast for Newark and upsert into weather_hourly.
Run on a schedule (hourly) by the GitHub Actions workflow in /infra.
"""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from db import get_session, init_db
from models import WeatherHourly
from weather_client import fetch_hourly_forecast, parse_period


def run() -> int:
    init_db()
    periods = fetch_hourly_forecast()
    now = datetime.now(timezone.utc)
    rows_written = 0

    with get_session() as session:
        for period in periods:
            parsed = parse_period(period)
            stmt = insert(WeatherHourly).values(
                forecast_time=parsed["forecast_time"],
                temperature_f=parsed["temperature_f"],
                wind_speed_mph=parsed["wind_speed_mph"],
                precipitation_probability_pct=parsed["precipitation_probability_pct"],
                short_forecast=parsed["short_forecast"],
                collected_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[WeatherHourly.forecast_time],
                set_={
                    "temperature_f": parsed["temperature_f"],
                    "wind_speed_mph": parsed["wind_speed_mph"],
                    "precipitation_probability_pct": parsed["precipitation_probability_pct"],
                    "short_forecast": parsed["short_forecast"],
                    "collected_at": now,
                },
            )
            session.execute(stmt)
            rows_written += 1

    print(f"[poll_weather] upserted {rows_written} hourly forecast rows")
    return rows_written


if __name__ == "__main__":
    run()
