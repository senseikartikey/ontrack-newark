"""
Client for NJ Transit's RailData API.

Verified against the real API on 2026-08-01 (Kartikey's RailData access was
approved) and cross-checked against a public reference implementation's actual
source (github.com/jtarrio/raildata/api/{api,methods}.go), not just its README:
- Base URL: https://raildata.njtransit.com/api/TrainData (test env at
  testraildata.njtransit.com uses the same path shape).
- Every method is POST, multipart/form-data (not JSON, not urlencoded), at
  <base>/<methodName> e.g. .../TrainData/getToken.
- getToken: request {username, password} -> response {Authenticated, UserToken}.
- getVehicleData: request {token} -> response is a BARE JSON array (no wrapper
  object) of train objects with fields ID, TRAIN_LINE, DIRECTION,
  ICS_TRACK_CKT, LAST_MODIFIED, SCHED_DEP_TIME, SEC_LATE, NEXT_STOP,
  LONGITUDE, LATITUDE.
- getStationMSG: request {token} -> response is a BARE JSON array of alert
  objects with fields MSG_TYPE, MSG_TEXT, MSG_RICHTEXT, MSG_PUBDATE, MSG_ID,
  MSG_AGENCY, MSG_SOURCE, MSG_STATION_SCOPE, MSG_LINE_SCOPE (e.g.
  "*North Jersey Coast Line" -- note the leading asterisk and inconsistent
  casing like "MontClair-Boonton Line"), MSG_PUBDATE_UTC, MSG_URL.
- getTrainSchedule: request {token, station} (station = NJT's own 2-character
  station code, e.g. "NP" for Newark Penn Station -- a third, distinct
  station-identifier space from both the live feed's station-name strings and
  static GTFS's numeric stop_id; see poll_track_assignments.py) -> response is a
  wrapper object {STATION_2CHAR, STATIONNAME, STATIONMSGS, ITEMS: [...]}, where
  each ITEMS entry has fields including SCHED_DEP_DATE, DESTINATION, TRACK,
  LINE, TRAIN_ID, LINECODE, LINEABBREVIATION, STOPS.

Real, live-discovered 2026-08-02: NJT RailData enforces a very low account-wide
DAILY quota on `getToken` issuance specifically -- a real getToken call returned
`{"errorMessage":"Daily usage limit:10. Your current daily usage: 11"}`. Confirmed
that only *successful* token issuance counts against the quota (repeated failed
calls while already over quota did not increment the reported usage number), and
that this applies to every endpoint, not just getTrainSchedule -- getVehicleData
failed with the identical getToken error once the quota was exhausted. Given the
existing production cadence (every 5 minutes, via GitHub Actions -- see
/.github/workflows/ingest.yml) runs each poller script as a brand-new process with
no cross-process memory, the original in-memory-only `_Token` cache below meant
every single scheduled invocation of every NJT-authenticated script minted its own
fresh token rather than reusing one across the ~25-minute assumed TTL -- 2 scripts
x 12 cycles/hour was already 24 token requests/hour on its own, several times the
entire daily quota within the first hour of any day. `_ensure_token` now checks a
DB-backed cache (`NjtTokenCache` in models.py) before calling getToken, and persists
a freshly issued token back to it -- shared by every poller process, not just
within one script's own lifetime. See ENGINEERING_LOG.md's 2026-08-02 entry.

Re-checked live 2026-08-02 (later the same day, prompted by research into a
comparable open-source project that uses a different endpoint,
`getTrainSchedule19Rec` -- see `get_train_schedule_19rec` below): a fresh, real
`getToken` call still returned the exact same error, `{"errorMessage":"Daily usage
limit:10. Your current daily usage: 11"}` -- unchanged from the original discovery,
confirming the quota had NOT reset in the intervening time and is very likely a
rolling/sticky window rather than a simple calendar-day boundary (a calendar-day
reset would be expected to have cleared this by now). No live NJT API calls beyond
this one probe were made this session as a result.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from config import NJT_PASSWORD, NJT_RAILDATA_BASE_URL, NJT_USERNAME

TOKEN_REFRESH_MARGIN_SECONDS = 60

# How long a freshly issued token is assumed to remain valid before this client
# proactively refreshes it. NJT doesn't return an explicit expiry in the
# getToken response (see _fetch_token below), so this has always been a guess --
# but it must be a guess sized against the real, live-confirmed constraint: NJT
# RailData enforces an account-wide DAILY quota of 10 successful `getToken`
# issuances (see module docstring's "Real, live-discovered 2026-08-02" note).
#
# The math this used to ignore: 24h / 10 tokens = 2.4h is the theoretical max
# sustainable refresh interval if *every single* daily quota unit were spent on
# this one purpose alone. The original 25-minute assumed TTL predates that
# discovery -- it was picked before the quota was known to exist at all, and at
# 25 minutes, even with the DB-backed cache in NjtTokenCache sharing one token
# across processes, a fresh token still gets requested roughly every 25 minutes
# regardless of cache-sharing -- ~57 real getToken calls/day, nearly 6x the
# actual 10/day quota, exhausting it within the first few hours of any day.
#
# 6 hours is used instead: ~4 refreshes/day out of the 10 available (24h / 6h),
# leaving real margin below the 2.4h theoretical ceiling for (a) manual
# `workflow_dispatch` runs outside the regular schedule, (b) local dev/testing
# against the real API, and (c) this project now having three separate
# NJT-authenticated scripts (poll_gtfs_rt.py, poll_alerts.py,
# poll_track_assignments.py) that could each independently trigger a refresh if
# the persistent cache ever misses (e.g. DB unreachable) -- not just one script
# as when 25 minutes was first chosen.
#
# This is still a guess, not an empirically confirmed server-side TTL -- NJT
# simply doesn't publish one. It's a much safer guess than 25 minutes because
# it's sized against the known 10/day quota rather than picked arbitrarily. If
# tokens are ever found to actually expire before this 6-hour window in
# practice, that would surface as real `getToken`/authentication errors in the
# scheduled workflow's logs partway through a token's assumed lifetime -- THAT
# real signal is the right reason to shorten this constant, not a guess made in
# a vacuum with no evidence either way.
TOKEN_ASSUMED_TTL_SECONDS = 6 * 60 * 60


@dataclass
class _Token:
    value: str
    expires_at: float  # unix timestamp


def _multipart(fields: dict[str, str]) -> dict[str, tuple[None, str]]:
    """NJT's API expects multipart/form-data, not the default urlencoded body --
    this is the standard `requests` trick for sending plain form fields as
    multipart (None filename = not a file attachment)."""
    return {k: (None, v) for k, v in fields.items()}


class NJTransitRailClient:
    def __init__(
        self,
        username: str = NJT_USERNAME,
        password: str = NJT_PASSWORD,
        base_url: str = NJT_RAILDATA_BASE_URL,
        session: requests.Session | None = None,
        use_persistent_token_cache: bool = True,
    ):
        if not username or not password:
            raise ValueError(
                "NJT_USERNAME/NJT_PASSWORD are not set. Register at "
                "https://developer.njtransit.com/registration/ and add them to .env."
            )
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._token: _Token | None = None
        # See module docstring's "Real, live-discovered 2026-08-02" note: NJT's
        # getToken quota is too tight to mint a fresh token per process invocation.
        # Defaults on so every existing/new poller script benefits automatically
        # without needing its own changes. Off switch exists for tests/tools that
        # don't want a DB dependency (e.g. no DATABASE_URL configured at all).
        self._use_persistent_token_cache = use_persistent_token_cache

    def _ensure_token(self) -> str:
        if self._token and self._token.expires_at - TOKEN_REFRESH_MARGIN_SECONDS > time.time():
            return self._token.value

        if self._use_persistent_token_cache:
            cached = self._load_cached_token()
            if cached and cached.expires_at - TOKEN_REFRESH_MARGIN_SECONDS > time.time():
                self._token = cached
                return self._token.value

        self._token = self._fetch_token()
        if self._use_persistent_token_cache:
            self._save_cached_token(self._token)
        return self._token.value

    def _load_cached_token(self) -> _Token | None:
        """Best-effort read of a still-valid token from `njt_token_cache`. Any
        failure (DB unreachable, table not created yet, DATABASE_URL unset) falls
        back to fetching a fresh token rather than raising -- persistence is an
        optimization on top of a working client, not a hard dependency of it."""
        try:
            from db import get_session
            from models import NjtTokenCache

            with get_session() as session:
                row = session.get(NjtTokenCache, 1)
                if row is None:
                    return None
                return _Token(value=row.token, expires_at=row.expires_at.timestamp())
        except Exception:
            return None

    def _save_cached_token(self, token: _Token) -> None:
        """Best-effort write-back of a freshly issued token, upserted into the
        single-row `njt_token_cache` table so the next process invocation (a
        different script, a different scheduled run) can reuse it instead of
        minting a new one. Failure here is non-fatal -- this process still has a
        working in-memory token for its own remaining lifetime either way."""
        try:
            from sqlalchemy.dialects.postgresql import insert

            from db import get_session
            from models import NjtTokenCache

            expires_at_dt = datetime.fromtimestamp(token.expires_at, tz=timezone.utc)
            with get_session() as session:
                stmt = insert(NjtTokenCache).values(
                    id=1, token=token.value, expires_at=expires_at_dt
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={"token": token.value, "expires_at": expires_at_dt},
                )
                session.execute(stmt)
        except Exception:
            pass

    def _fetch_token(self) -> _Token:
        resp = self._session.post(
            f"{self._base_url}/getToken",
            files=_multipart({"username": self._username, "password": self._password}),
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if not body.get("Authenticated"):
            raise RuntimeError(f"NJT RailData authentication failed: {body!r}")
        token_value = body.get("UserToken")
        if not token_value:
            raise RuntimeError(f"Unexpected token response shape: {body!r}")
        # NJT doesn't return an explicit expiry -- refresh proactively on the
        # assumed TTL above (see TOKEN_ASSUMED_TTL_SECONDS for the quota math
        # this is sized against) rather than relying on one.
        expires_at = time.time() + TOKEN_ASSUMED_TTL_SECONDS
        return _Token(value=token_value, expires_at=expires_at)

    def get_vehicle_data(self) -> list[dict]:
        """Fetch live rail vehicle/train position + status data. Returns a bare
        list of train dicts (see module docstring for fields) -- not wrapped."""
        token = self._ensure_token()
        resp = self._session.post(
            f"{self._base_url}/getVehicleData",
            files=_multipart({"token": token}),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_station_messages(self) -> list[dict]:
        """Fetch active system-wide service alerts/messages. Returns a bare list
        of alert dicts (see module docstring for fields) -- not wrapped."""
        token = self._ensure_token()
        resp = self._session.post(
            f"{self._base_url}/getStationMSG",
            files=_multipart({"token": token}),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_train_schedule(self, station: str) -> dict:
        """Fetch scheduled/estimated departures for a given station."""
        token = self._ensure_token()
        resp = self._session.post(
            f"{self._base_url}/getTrainSchedule",
            files=_multipart({"token": token, "station": station}),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_train_schedule_19rec(self, station: str) -> dict:
        """Fetch scheduled/estimated departures for a given station via NJT
        RailData's `getTrainSchedule19Rec` endpoint -- same request shape as
        `get_train_schedule` above (POST, multipart {token, station}, same
        2-character station-code space), added 2026-08-02 after a public
        reference project (`usernamemason/train-scraper`, README claims
        85%+ track-capture since Feb 2026) reported using this endpoint
        instead of `getTrainSchedule` for potentially richer/fresher data.

        NOT YET LIVE-TESTED as of 2026-08-02: NJT RailData's account-wide
        10/day `getToken` quota was still exhausted (confirmed via a real
        `getToken` call returning the same `Daily usage limit:10. Your
        current daily usage: 11` error already documented in this module's
        docstring) when this method was added, so this implementation is
        code-complete and follows `get_train_schedule`'s exact working
        pattern, but its response shape/content has NOT been empirically
        compared against `get_train_schedule`'s. Do not assume it returns
        more records, fresher data, or different TRACK values for any
        station (including NY Penn) until a real side-by-side comparison is
        done once the quota resets -- see ENGINEERING_LOG.md's 2026-08-02
        entry. `poll_track_assignments.py` deliberately still uses
        `get_train_schedule`, not this method, until that comparison
        produces real, positive evidence one way or the other.
        """
        token = self._ensure_token()
        resp = self._session.post(
            f"{self._base_url}/getTrainSchedule19Rec",
            files=_multipart({"token": token, "station": station}),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
