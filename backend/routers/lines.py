"""
Week 1 scope: live-status endpoints only, reading directly from trip_updates.
/predict and /scorecard are added in Week 3-4 once /ml exists (see AGENTS.md, CLAUDE.md).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import LINE_DISPLAY_NAMES, NEWARK_AREA_LINES
from db import get_db
from models import TripUpdate

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
