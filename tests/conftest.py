"""Shared fixtures: settings, API client, test data and browser."""

from collections.abc import Generator, Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver

from framework.api.client import BettingApiClient
from framework.config import Settings, load_settings
from framework.driver import create_chrome_driver
from framework.money import to_decimal

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"

_PHASE_REPORTS = pytest.StashKey[dict[str, pytest.TestReport]]()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Keep each phase's report on the test item so a fixture can tell if the test failed."""
    report = yield
    item.stash.setdefault(_PHASE_REPORTS, {})[report.when] = report
    return report


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def api(settings: Settings) -> BettingApiClient:
    return BettingApiClient(settings.base_url, settings.user_id)


@pytest.fixture(scope="session")
def upcoming_match(api: BettingApiClient) -> dict[str, Any]:
    """First match with a kickoff date after today.

    The match list also contains past matches (BUG-02), so the first entry
    cannot be used as a valid bet target.
    """
    today = date.today().isoformat()
    matches = api.get_matches().json()
    return next(match for match in matches if match["kickoffDate"] > today)


@pytest.fixture
def starting_balance(api: BettingApiClient) -> Decimal:
    """Reset the balance and return the amount that was actually stored.

    The reset response is not used: it reports a different amount than the
    one persisted (BUG-07). Tests assert on changes relative to this value.
    """
    api.reset_balance().raise_for_status()
    return to_decimal(api.get_balance().json()["balance"])


@pytest.fixture
def driver(settings: Settings, request: pytest.FixtureRequest) -> Iterator[WebDriver]:
    """Fresh browser per test. Saves a screenshot to artifacts/ when the test body fails."""
    browser = create_chrome_driver(headless=settings.headless)
    yield browser
    try:
        report = request.node.stash.get(_PHASE_REPORTS, {}).get("call")
        if report is not None and report.failed:
            ARTIFACTS_DIR.mkdir(exist_ok=True)
            browser.save_screenshot(str(ARTIFACTS_DIR / f"{request.node.name}.png"))
    finally:
        browser.quit()
