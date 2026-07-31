"""
Client for NJ Transit's RailData API.

IMPORTANT — this module is a best-effort scaffold, not a verified integration.
NJ Transit's RailData API docs are only visible after logging into
https://developer.njtransit.com/registration/ and requesting RailData access.
The auth pattern below (username/password -> bearer token, auto-refreshed) matches
the shape used by public reference clients (e.g. github.com/jtarrio/raildata), but the
exact endpoint paths are NOT yet confirmed. Every TODO below must be checked against
the real API reference once you're registered, before this will actually work.
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
        # TODO(data-engineer-agent): confirm the real token endpoint path and the
        # expected request/response shape (field names for token + expiry) against
        # the developer portal's RailData API reference.
        resp = self._session.post(
            f"{self._base_url}/TrainData/getToken",
            data={"username": self._username, "password": self._password},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        # TODO: confirm actual response field names -- assuming a shape like
        # {"UserToken": "...", "ExpirationTime": "..."} pending real docs.
        token_value = body.get("UserToken") or body.get("token")
        if not token_value:
            raise RuntimeError(f"Unexpected token response shape: {body!r}")
        # Fall back to a conservative 25-minute TTL if no expiry is present, so we
        # refresh proactively rather than relying on an unconfirmed field.
        expires_at = time.time() + 25 * 60
        return _Token(value=token_value, expires_at=expires_at)

    def get_vehicle_data(self) -> dict:
        """Fetch live rail vehicle/train position + status data."""
        token = self._ensure_token()
        # TODO(data-engineer-agent): confirm real endpoint path -- this is a
        # best-effort guess based on the method name used by public reference
        # clients (`GetVehicleData`), not a verified NJT path.
        resp = self._session.post(
            f"{self._base_url}/TrainData/getVehicleData",
            data={"token": token},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_train_schedule(self, station: str) -> dict:
        """Fetch scheduled/estimated departures for a given station."""
        token = self._ensure_token()
        # TODO(data-engineer-agent): confirm real endpoint path and station
        # identifier format (station code vs. full name) against the real docs.
        resp = self._session.post(
            f"{self._base_url}/TrainData/getTrainSchedule",
            data={"token": token, "station": station},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
