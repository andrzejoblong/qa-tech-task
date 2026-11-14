"""Thin HTTP client for the Sports Betting API."""

from typing import Any

import requests

USER_ID_HEADER = "x-user-id"
DEFAULT_TIMEOUT_S = 15


class BettingApiClient:
    """One method per endpoint, each returning the raw response.

    Methods do not raise on 4xx/5xx. Validation tests assert on the status code
    and the error body, so the test decides what counts as a failure.
    """

    def __init__(self, base_url: str, user_id: str, timeout: float = DEFAULT_TIMEOUT_S) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers[USER_ID_HEADER] = user_id

    def get_matches(self) -> requests.Response:
        return self._request("GET", "/api/matches")

    def get_balance(self) -> requests.Response:
        return self._request("GET", "/api/balance")

    def place_bet(self, payload: Any) -> requests.Response:
        """POST /api/place-bet. The payload is sent as given so tests can send invalid bodies."""
        return self._request("POST", "/api/place-bet", json=payload)

    def reset_balance(self) -> requests.Response:
        return self._request("POST", "/api/reset-balance")

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self._base_url}{path}"
        return self._session.request(method, url, timeout=self._timeout, **kwargs)
