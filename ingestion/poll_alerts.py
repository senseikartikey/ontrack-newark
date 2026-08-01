"""
Entrypoint: fetch active NJ Transit service alerts and upsert into service_alerts.
Run on the same schedule as poll_gtfs_rt.py (every 5 min) by the GitHub Actions
workflow in /infra.

Verified live on 2026-08-01 against the real getStationMSG endpoint -- see
njt_client.py's docstring for the confirmed response shape. Only alerts whose
MSG_LINE_SCOPE resolves to a Newark-area line (via config.match_line_scope) are
kept; system-wide or other-line alerts are dropped to stay in scope.
"""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from config import match_line_scope
from db import get_session, init_db
from models import ServiceAlert
from njt_client import NJTransitRailClient

# MSG_PUBDATE_UTC looks like "7/31/2026 11:26:31 PM" -- already UTC, so no
# timezone conversion needed (unlike poll_gtfs_rt.py's Eastern-local timestamps).
_MSG_TIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"


def _parse_utc_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _MSG_TIME_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def run() -> int:
    init_db()
    client = NJTransitRailClient()
    messages = client.get_station_messages()
    now = datetime.now(timezone.utc)
    rows_written = 0

    with get_session() as session:
        for msg in messages:
            code = match_line_scope(msg.get("MSG_LINE_SCOPE", ""))
            if code is None:
                continue

            alert_id = str(msg.get("MSG_ID", ""))
            if not alert_id:
                continue

            stmt = insert(ServiceAlert).values(
                alert_id=alert_id,
                line=code,
                header_text=msg.get("MSG_TEXT", ""),
                description_text=msg.get("MSG_URL"),
                active_from=_parse_utc_time(msg.get("MSG_PUBDATE_UTC")),
                active_to=None,
                collected_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["alert_id"],
                set_={
                    "line": code,
                    "header_text": msg.get("MSG_TEXT", ""),
                    "description_text": msg.get("MSG_URL"),
                    "active_from": _parse_utc_time(msg.get("MSG_PUBDATE_UTC")),
                    "collected_at": now,
                },
            )
            session.execute(stmt)
            rows_written += 1

    print(f"[poll_alerts] wrote {rows_written} Newark-area alert rows (of {len(messages)} total system-wide)")
    return rows_written


if __name__ == "__main__":
    run()
