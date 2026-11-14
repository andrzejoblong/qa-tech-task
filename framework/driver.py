"""Chrome WebDriver factory."""

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

# The feature is desktop-only with a fixed right-side bet slip, so the viewport
# is pinned: the layout is the same on a laptop and on a CI runner.
WINDOW_SIZE = "1440,900"


def create_chrome_driver(*, headless: bool) -> WebDriver:
    """Start Chrome. Selenium Manager fetches the matching chromedriver on first use."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    return webdriver.Chrome(options=options)
