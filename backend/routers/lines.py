from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import (
    LINE_DISPLAY_NAMES,
    RAIL_LINES,
    RISK_LOW_MAX_SECONDS,
    RISK_MEDIUM_MAX_SECONDS,
)
from db import get_db
from models import DelayBaseline, MLPrediction, TripUpdate

router = APIRouter(prefix="/lines", tags=["lines"])

LIVE_WINDOW_MINUTES = 30


@router.get("")
def list_lines():
    return {
        "lines": [
            {"code": code, "display_name": LINE_DISPLAY_NAMES.get(code, code)}
            for code in RAIL_LINES
        ]
    }


@router.get("/{line}/live")
def get_live_status(line: str, db: Session = Depends(get_db)):
    if line not in RAIL_LINES:
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


def get_current_risk(line: str, db: Session, now: datetime | None = None) -> dict:
    """
    Shared "what's the current predicted risk for this line" helper -- used by both
    GET /lines/{line}/predict and GET /lines/{line}/advisory (advisories.py) so the
    preference order lives in exactly one place.

    Prefers the v2 LightGBM model (ml_predictions) if train_model.py has written
    a bucket for this line/hour/day-of-week -- it's only ever written once the
    model both cleared a minimum training-data threshold and beat the v1
    statistical baseline on a held-out test set, so "it exists" already implies
    "it's trustworthy enough to prefer." Falls back to the v1 baseline, then to
    an honest "insufficient_data" status rather than fabricating a number.

    Does not validate `line` against RAIL_LINES -- callers are expected to
    do that themselves (they each need to raise their own HTTPException anyway).
    """
    now = now or datetime.now(timezone.utc)

    ml_prediction = db.get(MLPrediction, (line, now.hour, now.weekday()))
    if ml_prediction is not None:
        return {
            "line": line,
            "status": "ok",
            "source": "ml_model",
            "model_version": ml_prediction.model_version,
            "predicted_delay_seconds": round(ml_prediction.predicted_delay_seconds),
            "risk_level": _risk_level(ml_prediction.predicted_delay_seconds),
            "sample_size": ml_prediction.sample_size,
            "mae_seconds": round(ml_prediction.mae_seconds, 1),
            "baseline_mae_seconds": round(ml_prediction.baseline_mae_seconds, 1),
            "computed_at": ml_prediction.computed_at,
        }

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
        "source": "statistical_baseline",
        "predicted_delay_seconds": round(baseline.avg_delay_seconds),
        "risk_level": _risk_level(baseline.avg_delay_seconds),
        "sample_size": baseline.sample_size,
        "computed_at": baseline.computed_at,
    }


@router.get("/{line}/predict")
def get_predicted_risk(line: str, db: Session = Depends(get_db)):
    """Thin wrapper around get_current_risk() -- see that function's docstring for
    the ml_model/statistical_baseline/insufficient_data preference order."""
    if line not in RAIL_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    return get_current_risk(line, db)


# A trip counts "on time" using the same 60s threshold the frontend's live-status
# badge uses, so the scorecard and the live view never disagree about what
# "on time" means.
ON_TIME_THRESHOLD_SECONDS = 60


def _on_time_pct(db: Session, line: str, days: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # One reading per (trip, calendar day) -- a trip polled every 5 min while
    # sitting at the same next-stop would otherwise count many times over.
    latest_per_trip_day = (
        select(
            TripUpdate.trip_id,
            func.date(TripUpdate.scheduled_time).label("trip_date"),
            func.max(TripUpdate.collected_at).label("latest_collected_at"),
        )
        .where(TripUpdate.line == line, TripUpdate.scheduled_time >= cutoff)
        .group_by(TripUpdate.trip_id, func.date(TripUpdate.scheduled_time))
        .subquery()
    )

    delays = db.execute(
        select(TripUpdate.delay_seconds).join(
            latest_per_trip_day,
            (TripUpdate.trip_id == latest_per_trip_day.c.trip_id)
            & (func.date(TripUpdate.scheduled_time) == latest_per_trip_day.c.trip_date)
            & (TripUpdate.collected_at == latest_per_trip_day.c.latest_collected_at),
        )
    ).scalars().all()

    sample_size = len(delays)
    if sample_size == 0:
        return {"sample_size": 0, "on_time_pct": None}

    on_time = sum(1 for d in delays if d is not None and d <= ON_TIME_THRESHOLD_SECONDS)
    return {"sample_size": sample_size, "on_time_pct": round(100 * on_time / sample_size, 1)}


@router.get("/{line}/scorecard")
def get_scorecard(line: str, db: Session = Depends(get_db)):
    """Rolling 7/30-day on-time percentage. `sample_size` is always included so
    the frontend can hedge confidence on a small sample rather than presenting
    a percentage from a handful of trips as if it were a stable statistic."""
    if line not in RAIL_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    return {
        "line": line,
        "rolling_7_day": _on_time_pct(db, line, 7),
        "rolling_30_day": _on_time_pct(db, line, 30),
    }
