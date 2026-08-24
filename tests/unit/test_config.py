"""Unit tests for the harness configuration helpers."""

from pathlib import Path

import pytest

from harness.config import Settings


def test_defaults_apply_when_environment_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("BASE_URL", "HEADLESS", "SLOW_MO_MS", "DEFAULT_TIMEOUT_MS", "ARTIFACTS_DIR"):
        monkeypatch.delenv(name, raising=False)

    config = Settings.from_env()

    assert config.base_url == "http://localhost:8000"
    assert config.headless is True
    assert config.slow_mo_ms == 0
    assert config.default_timeout_ms == 5_000
    assert config.artifacts_dir.name == "artifacts"


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://staging.example.com/")
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setenv("SLOW_MO_MS", "250")
    monkeypatch.setenv("ARTIFACTS_DIR", "out")

    config = Settings.from_env()

    assert config.base_url == "https://staging.example.com"
    assert config.headless is False
    assert config.slow_mo_ms == 250
    assert config.artifacts_dir == Path(config.artifacts_dir.parent, "out")


def test_malformed_values_fall_back_to_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLOW_MO_MS", "not-a-number")

    assert Settings.from_env().slow_mo_ms == 0


def test_url_joins_paths_without_doubling_slashes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://example.com/")

    config = Settings.from_env()

    assert config.url("/login") == "https://example.com/login"
    assert config.url("login") == "https://example.com/login"
    assert config.url() == "https://example.com/"
