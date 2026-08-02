from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import RAIL_LINES
from db import get_db
from models import ServiceAlert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(line: str | None = Query(default=None), db: Session = Depends(get_db)):
    if line is not None and line not in RAIL_LINES:
        raise HTTPException(status_code=404, detail=f"Unknown line: {line}")

    query = select(ServiceAlert).order_by(ServiceAlert.active_from.desc()).limit(50)
    if line is not None:
        query = query.where(ServiceAlert.line == line)

    rows = db.execute(query).scalars().all()
    return {
        "alerts": [
            {
                "alert_id": r.alert_id,
                "line": r.line,
                "header_text": r.header_text,
                "url": r.description_text,
                "active_from": r.active_from,
            }
            for r in rows
        ]
    }
