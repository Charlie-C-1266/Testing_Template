"""Template for tests against a real application.

These run only when `BASE_URL` is set (in the environment or `.env`), so the
suite stays green before the harness is pointed at anything:

    BASE_URL=https://staging.example.com uv run pytest -m e2e
"""

import os

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skipif(
    os.getenv("BASE_URL") is None,
    reason="set BASE_URL to run tests against a live application",
)


def test_home_page_responds(page: Page) -> None:
    # `base_url` comes from the browser context (see tests/e2e/conftest.py), so
    # relative paths are enough here.
    response = page.goto("/")

    assert response is not None, "navigation returned no response"
    assert response.ok, f"GET / returned {response.status}"
    expect(page.locator("body")).to_be_visible()
