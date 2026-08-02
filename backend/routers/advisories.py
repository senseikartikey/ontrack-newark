"""
Weather-aware proactive commute advisories (docs/PRD-v2.md Phase 1: "Weather-aware
proactive commute advisories" -- weather data has been ingested since Week 3 but was
never surfaced to riders). Cross-references upcoming forecast weather against the
line's current predicted delay risk (reusing routers.lines.get_current_risk, the same
ml_model/statistical_baseline/insufficient_data preference order /predict uses) and,
only when both a plausibly-adverse forecast AND a meaningfully elevated risk are
present, returns a short human-readable advisory string. Never fabricates urgency --
see the per-branch `status` values below, mirroring the honesty convention already
used by /predict's "insufficient_data".
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import LINE_DISPLAY_NAMES, RAIL_LINES
from db import get_db
from models import WeatherHourly
from routers.lines import get_current_risk

router = APIRouter(prefix="/lines", tags=["advisories"])

# How far ahead to look for adverse weather. 6 hours is long enough to give a rider a
# real heads-up before a commute later the same day (e.g. checking at 1pm ahead of a
# 5-6pm ride home) but short enough that we're relying on NWS's more reliable
# near-term forecast rather than a next-day outlook that's likely to change before it
# actually matters -- this endpoint is meant to answer "should I worry about *my*
# upcoming ride," not "what's the weather like tomorrow."
ADVISORY_WINDOW_HOURS = 6

# Adverse-weather thresholds. There's no pre-existing "adverse weather" convention
# anywhere else in this project (ingestion just stores raw NWS fields), so these were
# picked deliberately and conservatively, aimed at conditions plausibly correlated
# with rail delays (wet/slippery platforms and leaves-on-track in rain, catenary and
# tree-branch issues in high wind, low-traction issues in snow/ice) rather than
# flagging "any" precipitation:
#   - precipitation_probability_pct >= 60: NWS's own forecast wording shifts from
#     "chance"/"scattered" to "likely" right around 60-70% probability-of-precipitation
#     -- 60 is roughly where the forecast itself starts asserting rain is more likely
#     than not, not merely possible.
#   - wind_speed_mph >= 25: below NWS's own High Wind Watch threshold (typically
#     40mph sustained) but at/above the range where sustained wind starts to be
#     operationally relevant for catenary-powered rail -- chosen as an early-warning
#     threshold, deliberately more conservative than an official severe-weather
#     advisory level, since the point is a proactive heads-up, not a storm warning.
# Either condition alone is sufficient to call the forecast hour "adverse."
ADVERSE_PRECIP_PCT = 60
ADVERSE_WIND_MPH = 25

# Keyword fallback against NWS's free-text short_forecast, so a snow/ice/thunderstorm
# forecast still counts as adverse even in an hour where the numeric fields above
# happen to be under threshold (e.g. modest quantitative wind/precip readings on a
# forecast that still says "Snow Showers").
ADVERSE_FORECAST_KEYWORDS = ("snow", "ice", "sleet", "freezing", "thunderstorm")

# "Meaningfully elevated" predicted risk reuses the same low/medium/high bucketing
# /predict already uses (config.RISK_LOW_MAX_SECONDS / RISK_MEDIUM_MAX_SECONDS).
# "low" is deliberately excluded: pairing adverse weather with a risk level that's
# still bucketed "low" would be manufacturing urgency the data doesn't actually
# support, which CLAUDE.md/PRD-v2's honesty convention rules out.
ELEVATED_RISK_LEVELS = {"medium", "high"}


def _find_adverse_weather(db: Session, now: datetime) -> WeatherHourly | None:
    """Returns the earliest upcoming forecast hour (within ADVISORY_WINDOW_HOURS)
    that crosses an adverse-weather threshold, or None if none does."""
    window_end = now + timedelta(hours=ADVISORY_WINDOW_HOURS)
    rows = db.execute(
        select(WeatherHourly)
        .where(WeatherHourly.forecast_time >= now, WeatherHourly.forecast_time <= window_end)
        .order_by(WeatherHourly.forecast_time.asc())
    ).scalars().all()

    for row in rows:
        precip = row.precipitation_probability_pct or 0
        wind = row.wind_speed_mph or 0
        forecast_text = (row.short_forecast or "").lower()
        if (
            precip >= ADVERSE_PRECIP_PCT
            or wind >= ADVERSE_WIND_MPH
            or any(keyword in forecast_text for keyword in ADVERSE_FORECAST_KEYWORDS)
        ):
            return row
    return None


def _weather_summary(row: WeatherHourly) -> dict:
    return {
        "forecast_time": row.forecast_time,
        "short_forecast": row.short_forecast,
        "precipitation_probability_pct": row.precipitation_probability_pct,
        "wind_speed_mph": row.wind_speed_mph,
    }


def _weather_phrase(row: WeatherHourly) -> str:
    """Human-readable lead-in for the advisory message -- prefers NWS's own
    short_forecast text when present, falls back to the numeric fields."""
    if row.short_forecast:
        return row.short_forecast
    parts = []
    if row.precipitation_probability_pct is not None:
        parts.append(f"a {round(row.precipitation_probability_pct)}% chance of rain")
    if row.wind_speed_mph is not None:
        parts.append(f"winds around {round(row.wind_speed_mph)} mph")
    return " and ".join(parts) if parts else "adverse weather"


def _time_phrase(forecast_time: datetime, now: datetime) -> str:
    """Rough day-part label for the advisory message ('this evening', etc.)."""
    hours_ahead = (forecast_time - now).total_seconds() / 3600
    if hours_ahead <= 1:
        return "this hour"
    if forecast_time.date() != now.date():
        return "tomorrow"
    hour = forecast_time.hour
    if hour < 12:
        return "this morning"
    if hour < 17:
        return "this afternoon"
    return "this evening"


@router.get("/{line}/advisory")
def get_advisory(line: str, db: Session = Depends(get_db)):
    """
    Cross-references upcoming (next ADVISORY_WINDOW_HOURS) adverse weather for this
    line against its current predicted delay risk. `status`:
      - "ok": both an adverse-weather forecast hour and a meaningfully elevated
        predicted risk are present -- `message` is populated.
      - "no_advisory": data is sufficient but conditions don't warrant flagging
        anything (no adverse weather in the window, or adverse weather but risk
        isn't currently elevated).
      - "insufficient_data": no baseline/ml prediction exists yet for this
        line/hour/day-of-week, so we can't responsibly say anything either way --
        mirrors /predict's "insufficient_data" convention.
    """
    if line not in RAIL_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    now = datetime.now(timezone.utc)
    display_name = LINE_DISPLAY_NAMES.get(line, line)

    adverse_weather = _find_adverse_weather(db, now)
    risk = get_current_risk(line, db, now=now)

    if risk["status"] != "ok":
        return {
            "line": line,
            "status": "insufficient_data",
            "message": (
                f"Not enough historical delay data yet for {display_name} to say "
                "whether upcoming weather is likely to affect it."
            ),
            "weather": _weather_summary(adverse_weather) if adverse_weather else None,
        }

    if adverse_weather is None:
        return {
            "line": line,
            "status": "no_advisory",
            "message": (
                f"No adverse weather expected for {display_name} in the next "
                f"{ADVISORY_WINDOW_HOURS} hours."
            ),
            "risk_level": risk["risk_level"],
            "weather": None,
        }

    if risk["risk_level"] not in ELEVATED_RISK_LEVELS:
        return {
            "line": line,
            "status": "no_advisory",
            "message": (
                f"Adverse weather is expected, but {display_name}'s predicted delay "
                "risk isn't currently elevated."
            ),
            "risk_level": risk["risk_level"],
            "weather": _weather_summary(adverse_weather),
        }

    delay_minutes = round(risk["predicted_delay_seconds"] / 60)
    message = (
        f"{_weather_phrase(adverse_weather)} expected {_time_phrase(adverse_weather.forecast_time, now)} "
        f"-- {display_name} has historically run ~{delay_minutes} min behind around this time."
    )

    return {
        "line": line,
        "status": "ok",
        "message": message,
        "risk_level": risk["risk_level"],
        "predicted_delay_seconds": risk["predicted_delay_seconds"],
        "risk_source": risk["source"],
        "weather": _weather_summary(adverse_weather),
    }
