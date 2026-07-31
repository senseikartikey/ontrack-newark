from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import (
    LINE_DISPLAY_NAMES,
    NEWARK_AREA_LINES,
    RISK_LOW_MAX_SECONDS,
    RISK_MEDIUM_MAX_SECONDS,
)
from db import get_db
from models import DelayBaseline, TripUpdate

router = APIRouter(prefix="/lines", tags=["lines"])

LIVE_WINDOW_MINUTES = 30


@router.get("")
def list_lines():
    return {
        "lines": [
            {"code": code, "display_name": LINE_DISPLAY_NAMES.get(code, code)}
            for code in NEWARK_AREA_LINES
        ]
    }


@router.get("/{line}/live")
def get_live_status(line: str, db: Session = Depends(get_db)):
    if line not in NEWARK_AREA_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LIVE_WINDOW_MINUTES)

    # Most recent reading per trip_id within the live window.
    latest_per_trip = (
        select(
            TripUpdate.trip_id,
            func.max(TripUpdate.collected_at).label("latest_collected_at"),
        )
        .where(TripUpdate.line == line, TripUpdate.collected_at >= cutoff)
        .group_by(TripUpdate.trip_id)
        .subquery()
    )

    rows = db.execute(
        select(TripUpdate).join(
            latest_per_trip,
            (TripUpdate.trip_id == latest_per_trip.c.trip_id)
            & (TripUpdate.collected_at == latest_per_trip.c.latest_collected_at),
        )
    ).scalars().all()

    trips = [
        {
            "trip_id": r.trip_id,
            "direction": r.direction,
            "stop_id": r.stop_id,
            "scheduled_time": r.scheduled_time,
            "delay_seconds": r.delay_seconds,
        }
        for r in rows
    ]
    return {"line": line, "as_of": datetime.now(timezone.utc), "trips": trips}


def _risk_level(avg_delay_seconds: float) -> str:
    if avg_delay_seconds <= RISK_LOW_MAX_SECONDS:
        return "low"
    if avg_delay_seconds <= RISK_MEDIUM_MAX_SECONDS:
        return "medium"
    return "high"


@router.get("/{line}/predict")
def get_predicted_risk(line: str, db: Session = Depends(get_db)):
    """
    v1 statistical baseline only (see /ml/README.md) -- looks up the
    (line, hour_of_day, day_of_week) bucket for the current time. Returns an
    honest "insufficient_data" status rather than fabricating a number when
    /ml hasn't computed a trustworthy bucket yet (which, as of this endpoint
    shipping, is all of them -- ingestion has no real delay history yet).
    """
    if line not in NEWARK_AREA_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    now = datetime.now(timezone.utc)
    baseline = db.get(DelayBaseline, (line, now.hour, now.weekday()))

    if baseline is None:
        return {
            "line": line,
            "status": "insufficient_data",
            "message": "No baseline computed yet for this line/hour/day-of-week combination.",
        }

    return {
        "line": line,
        "status": "ok",
        "predicted_delay_seconds": round(baseline.avg_delay_seconds),
        "risk_level": _risk_level(baseline.avg_delay_seconds),
        "sample_size": baseline.sample_size,
        "computed_at": baseline.computed_at,
    }
