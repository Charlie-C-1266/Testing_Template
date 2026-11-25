# CI workflows

Everything lives in `.github/workflows/`. All workflows run with read-only
repository permissions and cancel superseded runs on the same branch.

## `ci.yml` — checks on every change

Runs on pushes to `main`, every pull request, and on demand. Steps: install
with `uv sync --frozen` (fails if `uv.lock` is stale), ruff, mypy, then the
whole pytest suite with coverage on Chromium. JUnit XML and anything under
`artifacts/` or `test-results/` are uploaded as the `test-artifacts` artifact,
pass or fail.

Live-target tests skip here because `BASE_URL` isn't set; that's intended —
pull requests stay independent of any deployed environment.

## `e2e-live.yml` — e2e (live target)

Runs the browser suite against a deployed application on Chromium, Firefox, and
WebKit in parallel, on weekdays at 05:00 UTC and on demand.

Setup:

1. **Settings → Secrets and variables → Actions → Variables**: add `BASE_URL`.
   Until it exists, scheduled runs are skipped rather than failing.
2. Credentials go under **Secrets**, then into the job's `env:` block (there's a
   commented example), then into `Settings` in `src/harness/config.py`.
3. To test a different URL once, use **Run workflow** and fill in `base_url`.

On failure, each browser uploads its Playwright traces and screenshots as
`e2e-<browser>`. Download it and open a trace with:

```bash
uv run playwright show-trace path/to/trace.zip
```

Change the `cron` line to run at a different time, or delete the `schedule`
block to run on demand only.

## `devcontainer.yml` — dev container

When `.devcontainer/`, `.python-version`, `pyproject.toml`, or `uv.lock` change,
builds the dev container with [devcontainers/ci](https://github.com/devcontainers/ci)
and runs `make check` inside it, so a broken image is caught before anyone opens
the repo.

## Dependabot

`.github/dependabot.yml` opens weekly, grouped PRs for Python packages
(`uv.lock`), GitHub Actions, the dev container base image, and dev container
features. The uv binary copied into the image by tag
(`COPY --from=ghcr.io/astral-sh/uv:<tag>` in `.devcontainer/Dockerfile`) may need
bumping by hand.

## Adding your own

Copy `ci.yml` as a starting point: checkout, `astral-sh/setup-uv`,
`uv sync --frozen`, then `uv run …`. Useful variations:

- **Only some tests:** `uv run pytest -m "e2e and not slow"`.
- **Faster runs:** add `-n auto` to parallelise with pytest-xdist.
- **Another browser:** `uv run playwright install --with-deps firefox`, then
  `--browser firefox`.
- **Against a preview deployment:** trigger on `deployment_status` and set
  `BASE_URL: ${{ github.event.deployment_status.environment_url }}`.
