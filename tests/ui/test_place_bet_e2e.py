"""E2E UI test: place a single bet (test plan TC-01)."""

from decimal import Decimal
from typing import Any

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver

from framework.api.client import BettingApiClient
from framework.config import Settings
from framework.money import payout, to_decimal
from framework.pages.betting_page import BettingPage

STAKE = Decimal("10.00")


class KnownDefect(Exception):
    """The application still shows a defect reported in docs/execution-report.md."""


@pytest.mark.xfail(
    raises=KnownDefect,
    strict=True,
    reason="BUG-03 stale UI balance, BUG-04 receipt payout, BUG-05 receipt team order",
)
def test_place_single_bet(
    driver: WebDriver,
    settings: Settings,
    api: BettingApiClient,
    upcoming_match: dict[str, Any],
    starting_balance: Decimal,
) -> None:
    """Why this test: placing a bet is the core money flow and the only journey
    that crosses every part of the feature (match list, bet slip, placement,
    receipt, balance). A defect here costs the user or the operator money, and
    it is the path that must be re-checked on every release, so it pays to
    automate it first.

    The test is in two parts. Plain assertions cover what works today; if one of
    them fails, the test fails. The receipt and the UI balance currently deviate
    from the specification (BUG-03, BUG-04, BUG-05). Those deviations raise
    KnownDefect, which is the only exception the xfail marker accepts. With
    strict=True the test turns red once the defects are fixed, which is the
    signal to remove the marker.
    """
    match = upcoming_match
    odds = to_decimal(match["odds"]["home"])
    expected_teams = f"{match['homeTeam']} vs {match['awayTeam']}"
    expected_payout = payout(STAKE, odds)

    page = BettingPage(driver)
    page.open(settings.app_url)
    assert page.wait_for_header_balance(starting_balance) == starting_balance

    bet_slip = page.select_odds(match["id"], "home")
    assert bet_slip.teams() == expected_teams
    assert bet_slip.market() == "Match Winner: Home"
    assert bet_slip.odds() == odds

    bet_slip.enter_stake(STAKE)
    assert bet_slip.potential_payout() == expected_payout

    receipt = bet_slip.place_bet()
    assert receipt.stake() == STAKE
    assert receipt.odds() == odds
    stored_balance = to_decimal(api.get_balance().json()["balance"])
    assert stored_balance == starting_balance - STAKE

    receipt_match = receipt.match()
    receipt_payout = receipt.payout()
    receipt.close()
    header_balance = page.wait_for_header_balance(stored_balance, timeout=3)

    deviations = []
    if receipt_match != expected_teams:
        deviations.append(f"BUG-05: receipt match is '{receipt_match}', not '{expected_teams}'")
    if receipt_payout != expected_payout:
        deviations.append(f"BUG-04: receipt payout is {receipt_payout}, not {expected_payout}")
    if header_balance != stored_balance:
        deviations.append(f"BUG-03: header balance is {header_balance}, not {stored_balance}")
    if deviations:
        raise KnownDefect("; ".join(deviations))
