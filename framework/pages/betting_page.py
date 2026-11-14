"""Main page: header and match list."""

from decimal import Decimal

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from framework.money import parse_euro
from framework.pages.base import DEFAULT_WAIT_S, BasePage
from framework.pages.bet_slip import BetSlip

HEADER_BALANCE = (By.ID, "header-balance")


class BettingPage(BasePage):
    def open(self, url: str) -> None:
        self._driver.get(url)
        self._visible(HEADER_BALANCE)

    def header_balance(self) -> Decimal:
        return parse_euro(self._text(HEADER_BALANCE))

    def wait_for_header_balance(
        self, expected: Decimal, timeout: float = DEFAULT_WAIT_S
    ) -> Decimal:
        """Give the header time to show ``expected`` and return what it shows in the end.

        The balance is fetched after the page renders, so the header shows €0.00
        for a moment. The caller asserts on the returned value.
        """
        try:
            WebDriverWait(self._driver, timeout).until(lambda _: self.header_balance() == expected)
        except TimeoutException:
            pass
        return self.header_balance()

    def select_odds(self, match_id: str, outcome: str) -> BetSlip:
        """Click an odds button. ``outcome`` is 'home', 'draw' or 'away'."""
        button = self._visible((By.ID, f"odds-{match_id}-{outcome}"))
        # The match list is long; centre the button so the fixed header cannot cover it.
        self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", button)
        button.click()
        return BetSlip(self._driver)
