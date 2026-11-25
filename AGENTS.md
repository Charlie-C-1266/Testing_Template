# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor, …)
working in this repository. Humans should start with the [README](README.md).

## What this is

A Python test harness: pytest + Playwright, dependencies managed by uv, run in a
dev container or on a bare machine. Tests live under `tests/`; reusable helpers
live in the installed package `src/harness/` (imported as `harness.*`).

## Commands

Always go through uv (or the Makefile, which wraps it). Never call `pip`, and
never create a virtualenv by hand.

| Task | Command |
| --- | --- |
| Install / sync deps | `uv sync` then `uv run playwright install chromium` |
| Everything CI runs | `make check` (lint + typecheck + tests) |
| Lint / autofix | `make lint` / `make format` |
| Type-check | `make typecheck` |
| Unit tests only | `make test-unit` |
| Browser tests only | `make test-e2e` |
| One test | `uv run pytest tests/path/test_file.py::test_name` |
| Add a dependency | `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (tooling) |
| Add from the curated catalog | `uv run python scripts/add_packages.py --packages pandas,httpx --yes` (`--list` shows it; it adds typing stubs too) |

**Definition of done:** `make check` passes. Do not report a change as finished
without running it.

## Layout and where new code goes

- `tests/unit/` — fast tests, no browser, no network.
- `tests/e2e/` — Playwright tests. Every test here is auto-marked `e2e` by
  `tests/e2e/conftest.py`; don't add the marker yourself.
- `tests/e2e/pages/` — page objects, one class per screen, subclassing
  `BasePage`. Locators are private attributes; public methods express intent.
- `src/harness/` — anything shared by more than one test module (config, API
  clients, data builders, custom assertions).
- `conftest.py` — fixtures shared by one directory's tests.

## Conventions

- Configuration comes from `harness.config.settings`. Never call `os.getenv` in a
  test. A new setting must be added to `Settings`, `.env.example`, and the
  configuration table in the README together.
- Locators: prefer `get_by_role`, `get_by_label`, `get_by_text`; use
  `get_by_test_id` only when nothing user-facing fits. No CSS/XPath chains.
- Assertions on the page use `expect(...)`, which retries; plain `assert` is for
  values you already have.
- Never `time.sleep` or `page.wait_for_timeout`. Wait on a condition instead.
- Tests own their data: each test sets up and tears down what it needs, so the
  suite runs in any order and under `pytest -n auto`.
- mypy runs in strict mode over `src/` and `tests/`. Annotate new code; don't add
  `# type: ignore` or loosen the config to make an error go away.
- Ruff owns formatting (line length 100). Run `make format` rather than
  hand-formatting.

## Don't

- Don't edit `uv.lock` by hand — change `pyproject.toml` via `uv add`/`uv remove`
  and let uv rewrite the lock. Commit both.
- Don't commit `.env`, credentials, or anything under `artifacts/` or
  `test-results/`.
- Don't point tests at production or put real credentials in test code; live
  targets come from `BASE_URL` and secrets from the environment.
- Don't delete the demo (`tests/e2e/fixtures/`, `example_page.py`,
  `test_example.py`) unless asked — it keeps a fresh clone green.
