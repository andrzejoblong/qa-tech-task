"""Success receipt: the modal shown after a bet is placed."""

from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from framework.money import parse_euro
from framework.pages.base import BasePage

MODAL = (By.ID, "modal-success")
MATCH = (By.ID, "modal-success-match")
STAKE = (By.ID, "modal-success-stake")
ODDS = (By.ID, "modal-success-odds")
PAYOUT = (By.ID, "modal-success-payout")
CLOSE = (By.ID, "modal-success-close")


class Receipt(BasePage):
    def match(self) -> str:
        return self._text(MATCH)

    def stake(self) -> Decimal:
        return parse_euro(self._text(STAKE))

    def odds(self) -> Decimal:
        return Decimal(self._text(ODDS))

    def payout(self) -> Decimal:
        return parse_euro(self._text(PAYOUT))

    def close(self) -> None:
        self._visible(CLOSE).click()
        self._wait.until(ec.invisibility_of_element_located(MODAL))
