# Thin wrappers over the commands in the README — every target is a one-liner
# you can also run by hand.
.DEFAULT_GOAL := help

.PHONY: help setup lint format typecheck test test-unit test-e2e test-headed trace clean

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup:  ## Install dependencies and the Chromium build Playwright needs
	uv sync
	uv run playwright install chromium

lint:  ## Lint and check formatting
	uv run ruff check .
	uv run ruff format --check .

format:  ## Apply formatting and autofixes
	uv run ruff format .
	uv run ruff check --fix .

typecheck:  ## Type-check with mypy
	uv run mypy

test:  ## Run the whole suite
	uv run pytest

test-unit:  ## Run everything except the browser tests
	uv run pytest -m "not e2e"

test-e2e:  ## Run the browser tests only
	uv run pytest -m e2e

test-headed:  ## Run the browser tests in a visible browser, slowed down
	uv run pytest -m e2e --headed --slowmo 250

trace:  ## Run the browser tests, recording a trace for each failure
	uv run pytest -m e2e --tracing retain-on-failure --output artifacts/traces

clean:  ## Remove caches and test artefacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml \
	       artifacts test-results
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
