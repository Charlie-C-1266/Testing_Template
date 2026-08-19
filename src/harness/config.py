"""Environment-driven configuration for the harness.

Values come from real environment variables first and a local `.env` file
second, so CI can override anything without editing files. Copy `.env.example`
to `.env` to set local defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# `override=False`: a variable already set in the environment always wins.
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable, accepting 1/true/yes/on."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back on a bad value."""
    raw = os.getenv(name)
    if raw is None or not raw.strip().lstrip("-").isdigit():
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    """Runtime knobs for a test run."""

    base_url: str
    headless: bool
    slow_mo_ms: int
    default_timeout_ms: int
    artifacts_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from the current environment."""
        return cls(
            base_url=os.getenv("BASE_URL", "http://localhost:8000").rstrip("/"),
            headless=_env_bool("HEADLESS", True),
            slow_mo_ms=_env_int("SLOW_MO_MS", 0),
            default_timeout_ms=_env_int("DEFAULT_TIMEOUT_MS", 5_000),
            artifacts_dir=PROJECT_ROOT / os.getenv("ARTIFACTS_DIR", "artifacts"),
        )

    def url(self, path: str = "/") -> str:
        """Join `path` onto the configured base URL."""
        return f"{self.base_url}/{path.lstrip('/')}"


# Import-time snapshot for convenience. Tests that need to exercise a different
# environment should call `Settings.from_env()` themselves after patching it.
settings = Settings.from_env()
