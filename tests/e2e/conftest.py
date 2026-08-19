"""Browser fixtures.

`pytest-playwright` supplies `page`, `context`, and `browser`; the fixtures below
override its configuration hooks so the harness settings (headless, slow-mo,
timeouts) drive the browser, and tag everything in this directory with the `e2e`
marker so `-m "not e2e"` reliably excludes it.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page

from harness.config import Settings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test under `tests/e2e/` as `e2e` without repeating a decorator."""
    for item in items:
        if Path(item.path).is_relative_to(Path(__file__).parent):
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict[str, Any],
    config: Settings,
    pytestconfig: pytest.Config,
) -> dict[str, Any]:
    """Launch the browser as the harness settings ask (`HEADLESS`, `SLOW_MO_MS`).

    Command-line flags still win: `--headed` and `--slowmo` are left alone when
    given, so a one-off debugging run needs no environment fiddling.
    """
    args = dict(browser_type_launch_args)
    if not pytestconfig.getoption("--headed"):
        args["headless"] = config.headless
    if not pytestconfig.getoption("--slowmo"):
        args["slow_mo"] = config.slow_mo_ms
    return args


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, Any],
    config: Settings,
    pytestconfig: pytest.Config,
) -> dict[str, Any]:
    """Point every context at `BASE_URL` so tests can navigate with relative paths.

    An explicit `--base-url` on the command line takes precedence.
    """
    return {
        **browser_context_args,
        "base_url": pytestconfig.getoption("--base-url") or config.base_url,
        "viewport": {"width": 1280, "height": 800},
    }


@pytest.fixture(autouse=True)
def _default_timeout(page: Page, config: Settings) -> None:
    """Apply the configured timeout to every action and assertion on the page."""
    page.set_default_timeout(config.default_timeout_ms)


@pytest.fixture
def local_fixture_page(page: Page) -> Iterator[Page]:
    """Open the bundled demo page — lets the example test run with no server."""
    page.goto((FIXTURES_DIR / "index.html").as_uri())
    yield page
