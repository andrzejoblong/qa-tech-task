"""Bet slip: the right-hand panel with the selection, the stake and the payout."""

from decimal import Decimal

from selenium.webdriver.common.by import By

from framework.money import parse_euro
from framework.pages.base import BasePage
from framework.pages.receipt import Receipt

TEAMS = (By.CLASS_NAME, "betSelectionTeams")
MARKET = (By.CLASS_NAME, "betSelectionMarket")
ODDS = (By.CLASS_NAME, "betSelectionOdds")
STAKE_INPUT = (By.ID, "bet-slip-stake-input")
POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
PLACE_BET = (By.ID, "bet-slip-place-bet")


class BetSlip(BasePage):
    def teams(self) -> str:
        return self._text(TEAMS)

    def market(self) -> str:
        return self._text(MARKET)

    def odds(self) -> Decimal:
        return Decimal(self._text(ODDS).removeprefix("Odds:").strip())

    def enter_stake(self, stake: Decimal) -> None:
        field = self._visible(STAKE_INPUT)
        field.clear()
        field.send_keys(str(stake))

    def potential_payout(self) -> Decimal:
        return parse_euro(self._text(POTENTIAL_PAYOUT))

    def place_bet(self) -> Receipt:
        self._visible(PLACE_BET).click()
        return Receipt(self._driver)
