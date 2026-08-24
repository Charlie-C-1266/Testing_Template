"""Example browser test against the bundled demo page.

It needs no server and no network, so `uv run pytest` passes on a fresh clone —
use it as the shape to copy, then delete it once real tests exist.
"""

from playwright.sync_api import Page, expect

from tests.e2e.pages.example_page import ExamplePage


def test_demo_page_loads(local_fixture_page: Page) -> None:
    example = ExamplePage(local_fixture_page)

    expect(example.heading).to_have_text("Test Harness Demo")


def test_submitting_the_form_shows_a_greeting(local_fixture_page: Page) -> None:
    example = ExamplePage(local_fixture_page)

    example.greet("Ada")

    expect(example.greeting).to_be_visible()
    expect(example.greeting).to_have_text("Hello, Ada!")
