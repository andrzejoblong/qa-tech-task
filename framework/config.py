"""Runtime settings, read from environment variables."""

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://qae-assignment-tau.vercel.app"


@dataclass(frozen=True)
class Settings:
    base_url: str
    user_id: str
    headless: bool

    @property
    def app_url(self) -> str:
        """UI entry point; the app takes the user id as a query parameter."""
        return f"{self.base_url}/?user-id={self.user_id}"


def load_settings() -> Settings:
    """Build settings from the environment.

    The user id has no default on purpose: it identifies one person's balance,
    so it stays out of the repository and a run without it fails immediately.
    """
    user_id = os.environ.get("QA_USER_ID", "").strip()
    if not user_id:
        raise RuntimeError("QA_USER_ID is not set. Export the user id issued with the assignment.")
    return Settings(
        base_url=os.environ.get("BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        user_id=user_id,
        headless=os.environ.get("HEADLESS", "1") != "0",
    )
