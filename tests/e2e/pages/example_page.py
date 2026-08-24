"""Page object for the bundled demo page (`tests/e2e/fixtures/index.html`).

Delete this once you have a real application to point at — it exists to show the
pattern and to give the template a test that passes out of the box.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from tests.e2e.pages.base_page import BasePage


class ExamplePage(BasePage):
    """The demo greeting form."""

    path = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._name_input = page.get_by_label("Your name")
        self._submit = page.get_by_role("button", name="Greet me")
        self._greeting = page.get_by_test_id("greeting")

    @property
    def heading(self) -> Locator:
        """The page's main heading."""
        return self.page.get_by_role("heading", level=1)

    @property
    def greeting(self) -> Locator:
        """The element that shows the greeting after submitting."""
        return self._greeting

    def greet(self, name: str) -> None:
        """Fill in a name and submit the form."""
        self._name_input.fill(name)
        self._submit.click()
