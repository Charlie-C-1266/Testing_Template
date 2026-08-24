#!/usr/bin/env bash
# Runs once, as the container user, after the dev container is created.
set -euo pipefail

echo "==> Syncing dependencies with uv"
uv sync

echo "==> Installing Playwright's Chromium build"
# OS-level dependencies were installed in the image; this only fetches the
# browser binaries into ~/.cache/ms-playwright (persisted by a named volume).
uv run playwright install chromium

echo "==> Ready. Try: make test"
