"""Fixtures shared by every test in the suite.

Test-type-specific fixtures live in the nearest conftest instead — see
`tests/e2e/conftest.py` for the browser ones.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from harness.config import Settings, settings


@pytest.fixture(scope="session")
def config() -> Settings:
    """The harness configuration for this run (env vars + `.env`)."""
    return settings


@pytest.fixture(scope="session")
def artifacts_dir(config: Settings) -> Iterator[Path]:
    """Directory for anything a test wants to keep: screenshots, dumps, logs."""
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    yield config.artifacts_dir
