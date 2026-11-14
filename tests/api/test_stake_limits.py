"""API test: stake limits at their boundaries (test plan TC-03)."""

from decimal import Decimal
from typing import Any

import pytest

from framework.api.client import BettingApiClient
from framework.money import to_decimal


@pytest.mark.parametrize(
    ("stake", "expected_status", "expected_error"),
    [
        (0.99, 422, "invalid_stake_min"),
        (1.00, 200, None),
        (1.01, 200, None),
        (100.00, 200, None),
        (100.01, 422, "invalid_stake_max"),
    ],
)
def test_stake_limits_are_enforced_by_the_api(
    api: BettingApiClient,
    upcoming_match: dict[str, Any],
    starting_balance: Decimal,
    stake: float,
    expected_status: int,
    expected_error: str | None,
) -> None:
    """Why this test: the stake limits cap how much one bet may risk, and the UI
    can be bypassed, so the server is the only place where the rule is binding.
    Boundary values are where an off-by-one error would sit, and the
    specification gives two different minimums (1.00 and 1.01), so both are
    pinned here. The check is fast and deterministic, which makes it a good
    guard to run on every change. It also verifies the money side: a rejected
    stake must not touch the balance, an accepted one must reduce it by exactly
    the stake.
    """
    response = api.place_bet({"matchId": upcoming_match["id"], "selection": "HOME", "stake": stake})

    assert response.status_code == expected_status
    assert response.json().get("error") == expected_error

    deducted = to_decimal(stake) if expected_status == 200 else Decimal("0")
    balance = to_decimal(api.get_balance().json()["balance"])
    assert balance == starting_balance - deducted
