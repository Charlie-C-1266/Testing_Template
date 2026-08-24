"""Smoke test: proves the suite is wired up and the harness package imports."""

import harness


def test_harness_package_is_importable() -> None:
    assert harness.settings.base_url
