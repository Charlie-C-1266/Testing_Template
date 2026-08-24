# Python Test Harness Template

A generic starting point for building a Python test harness: a dev container,
[uv](https://docs.astral.sh/uv/) for dependency management, and
[Playwright](https://playwright.dev/python/) wired up for browser tests.

Clone it, point it at whatever you need to test, and start writing tests — the
plumbing (environment, lint, types, CI, artefacts) is already done.

## What's in the box

- **Dev container** — Python 3.12 on Debian, uv preinstalled, and the OS packages
  Chromium needs baked into the image.
- **uv** — one lockfile, reproducible installs, no manual virtualenv juggling.
- **pytest + Playwright** — fixtures, a page-object layout, and a demo test that
  passes on a fresh clone with no server and no network.
- **ruff + mypy** — linting, formatting, and strict type checking, all configured.
- **GitHub Actions** — the same checks on every push and pull request.

## Quick start

### In the dev container (recommended)

1. Install [Docker](https://docs.docker.com/get-docker/) and VS Code with the
   [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   extension.
2. Open the folder in VS Code and choose **Reopen in Container**.
3. Wait for the first build. `post-create.sh` runs `uv sync` and downloads
   Chromium, so the suite is ready when the terminal appears.
4. Run the tests:

   ```bash
   make test
   ```

The container puts `.venv/bin` on `PATH`, so `pytest` works directly as well as
via `uv run pytest`.

### Without a dev container

You need [uv](https://docs.astral.sh/uv/getting-started/installation/); it will
fetch Python 3.12 itself if you don't have it.

```bash
uv sync                          # create .venv and install everything
uv run playwright install chromium   # download the browser
uv run pytest
```

On a bare Linux machine you may also need Chromium's system libraries:
`uv run playwright install --with-deps chromium` (needs sudo).

## Project structure

```
.
├── .devcontainer/
│   ├── Dockerfile          # base image + uv + Chromium's OS dependencies
│   ├── devcontainer.json   # editor settings, extensions, cache volumes
│   └── post-create.sh      # uv sync + browser download, run once on create
├── .github/workflows/ci.yml
├── src/harness/            # reusable helpers, importable as `harness.*`
│   ├── __init__.py
│   └── config.py           # settings from environment variables + .env
├── tests/
│   ├── conftest.py         # fixtures shared by every test
│   ├── unit/               # fast tests, no browser
│   └── e2e/
│       ├── conftest.py     # browser fixtures and the `e2e` marker
│       ├── fixtures/       # static demo page used by the example test
│       ├── pages/          # page objects (one class per screen)
│       ├── test_example.py           # runs offline against the demo page
│       └── test_app_under_test.py    # template for a real target; needs BASE_URL
├── .env.example            # copy to .env for local settings
├── Makefile                # shortcuts for everything below
├── pyproject.toml          # dependencies + pytest/ruff/mypy/coverage config
└── uv.lock                 # exact resolved versions — commit this
```

Anything shared by more than one test module belongs in `src/harness/`; anything
shared by one directory's tests belongs in that directory's `conftest.py`.

## Running tests

| Command | What it does |
| --- | --- |
| `make test` | The whole suite |
| `make test-unit` | Everything except browser tests (`-m "not e2e"`) |
| `make test-e2e` | Browser tests only (`-m e2e`) |
| `make test-headed` | Browser tests in a visible, slowed-down browser |
| `make trace` | Browser tests, recording a Playwright trace per failure |
| `uv run pytest -k greeting` | A single test by name |
| `uv run pytest -n auto` | In parallel across CPU cores (pytest-xdist) |

Tests under `tests/e2e/` are tagged `e2e` automatically — no decorator needed.

### Debugging a browser test

```bash
uv run pytest tests/e2e/test_example.py --headed --slowmo 500   # watch it happen
PWDEBUG=1 uv run pytest tests/e2e/test_example.py               # Playwright Inspector
uv run pytest -m e2e --tracing retain-on-failure --output artifacts/traces
uv run playwright show-trace artifacts/traces/**/trace.zip      # step through a failure
```

`--screenshot only-on-failure` and `--video retain-on-failure` are available too;
all of it lands under `--output`, which is git-ignored.

## Writing Playwright tests

Keep selectors in page objects and assertions in tests:

```python
# tests/e2e/pages/login_page.py
class LoginPage(BasePage):
    path = "/login"

    def __init__(self, page):
        super().__init__(page)
        self._email = page.get_by_label("Email")
        self._password = page.get_by_label("Password")
        self._submit = page.get_by_role("button", name="Sign in")

    def log_in(self, email: str, password: str) -> None:
        self._email.fill(email)
        self._password.fill(password)
        self._submit.click()
```

```python
# tests/e2e/test_login.py
def test_valid_credentials_reach_the_dashboard(page):
    login = LoginPage(page)
    login.open()

    login.log_in("user@example.com", "hunter2")

    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
```

A few conventions worth keeping:

- Prefer user-facing locators — `get_by_role`, `get_by_label`, `get_by_text` —
  and fall back to `data-testid` (`get_by_test_id`) only when nothing else fits.
  CSS/XPath chains break on every refactor.
- Assert with `expect(...)`, not bare `assert`: it retries until the timeout
  instead of racing the page.
- Never `sleep`. Playwright waits for actionability on its own; if you need a
  specific condition, `expect(...)` or `page.wait_for_*` it.
- Each test should set up and tear down its own data, so tests can run in any
  order and in parallel.

## Configuration

Settings come from environment variables, with a local `.env` (copied from
`.env.example`) as the fallback. Real environment variables always win, so CI can
override anything.

| Variable | Default | Purpose |
| --- | --- | --- |
| `BASE_URL` | `http://localhost:8000` | Application under test; sets the browser context's base URL |
| `HEADLESS` | `true` | Run the browser without a window |
| `SLOW_MO_MS` | `0` | Delay between browser actions, for watching a run |
| `DEFAULT_TIMEOUT_MS` | `5000` | Default Playwright action/assertion timeout |
| `ARTIFACTS_DIR` | `artifacts` | Where tests write screenshots and other keepsakes |

Read them through `harness.config.settings` rather than calling `os.getenv` in a
test, and add new ones to `Settings`, `.env.example`, and this table together.

## Managing dependencies

```bash
uv add requests                 # runtime dependency of the harness
uv add --dev pytest-timeout     # test-only tooling
uv remove requests
uv sync                         # bring .venv in line with uv.lock
uv lock --upgrade               # refresh the lockfile to newer versions
```

Commit `uv.lock` — CI installs with `uv sync --frozen` and fails if the lockfile
and `pyproject.toml` have drifted apart.

## Quality checks

```bash
make lint        # ruff check + ruff format --check
make format      # apply formatting and safe autofixes
make typecheck   # mypy (strict; tests may omit annotations)
make test
```

CI runs the same four on every push and pull request, then uploads test artefacts.
Run them locally before you push.

## Making it your own

1. Rename the project in `pyproject.toml` (`name`, `description`) and rename
   `src/harness/` if you want a different import name — update
   `[tool.hatch.build.targets.wheel]` to match.
2. Set `BASE_URL` in `.env` to the application you're testing.
3. Delete the demo: `tests/e2e/fixtures/`, `tests/e2e/pages/example_page.py`,
   `tests/e2e/test_example.py`, and the `local_fixture_page` fixture.
4. Build your first real test from `tests/e2e/test_app_under_test.py`.
5. Replace this README's title and intro with what your harness actually covers.
