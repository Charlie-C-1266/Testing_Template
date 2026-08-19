"""Base class for page objects."""

from __future__ import annotations

from playwright.sync_api import Page


class BasePage:
    """Common behaviour for every page object.

    Subclasses expose *intent* (`log_in`, `search_for`) and keep locators
    private, so a markup change is a one-line fix in one file.
    """

    path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        """Navigate to this page's path, relative to the configured base URL."""
        self.page.goto(self.path)

    def screenshot(self, destination: str) -> None:
        """Save a full-page screenshot, e.g. for a failure artefact."""
        self.page.screenshot(path=destination, full_page=True)
