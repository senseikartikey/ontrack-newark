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
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from config import NJT_PASSWORD, NJT_RAILDATA_BASE_URL, NJT_USERNAME

TOKEN_REFRESH_MARGIN_SECONDS = 60


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

    def _ensure_token(self) -> str:
        if self._token and self._token.expires_at - TOKEN_REFRESH_MARGIN_SECONDS > time.time():
            return self._token.value
        self._token = self._fetch_token()
        return self._token.value

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
        # NJT doesn't return an explicit expiry -- refresh proactively on a
        # conservative 25-minute assumed TTL rather than relying on one.
        expires_at = time.time() + 25 * 60
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
