"""Shared behaviour of page objects: explicit waits only, no sleeps."""

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Placing a bet takes a few seconds in the application, so the wait is generous.
DEFAULT_WAIT_S = 15

Locator = tuple[str, str]


class BasePage:
    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, DEFAULT_WAIT_S)

    def _visible(self, locator: Locator) -> WebElement:
        return self._wait.until(ec.visibility_of_element_located(locator))

    def _text(self, locator: Locator) -> str:
        return self._visible(locator).text.strip()
