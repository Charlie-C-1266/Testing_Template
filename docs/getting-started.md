# Getting started

From "Use this template" to a real test running in CI against your application.
Budget about half an hour. The [README](../README.md) is the reference; this is
the walkthrough.

## 1. Create your repository

On GitHub, click **Use this template → Create a new repository**, or:

```bash
gh repo create my-org/my-harness --template <owner>/<this-template> --private --clone
cd my-harness
```

## 2. Open it

**Dev container (recommended):** open the folder in VS Code and choose
**Reopen in Container**. The first build takes a few minutes; later rebuilds
reuse cached volumes. When the terminal appears, everything is installed.

**Bare machine:** install [uv](https://docs.astral.sh/uv/getting-started/installation/),
then:

```bash
make setup            # uv sync + download Chromium
```

Either way, confirm the starting point is green:

```bash
make check            # lint, type-check, and the full test suite
```

You should see the demo tests pass and `test_app_under_test.py` skipped.

## 3. Make it yours

1. In `pyproject.toml`, change `name` and `description`.
2. Replace the README's title and intro with what this harness covers.
3. Optionally rename `src/harness/` (update `[tool.hatch.build.targets.wheel]`
   and the imports to match).
4. Run `make packages` to add the libraries you plan to use — pandas,
   pydantic, httpx, pytest-asyncio and so on. It adds them with uv (typing
   stubs included) so they're in the container and the lockfile. You can come
   back to it any time.
5. Optionally run `make hooks` to lint and format on every commit.

## 4. Point it at your application

```bash
cp .env.example .env
```

Edit `.env` and uncomment `BASE_URL`, pointing it at the application you're
testing (a local dev server or a staging environment). Now:

```bash
make test-e2e
```

`test_home_page_responds` runs instead of being skipped. If it fails, check the
app is reachable from where the tests run — inside a dev container, `localhost`
is the container, not your machine; use `http://host.docker.internal:<port>`.

## 5. Write your first real test

1. Add a page object in `tests/e2e/pages/`, subclassing `BasePage`, with
   private locators and intent-revealing methods (see `example_page.py`).
2. Add a test in `tests/e2e/test_<feature>.py` that drives the page object and
   asserts with `expect(...)`.
3. Run it headed while you write it:

   ```bash
   uv run pytest tests/e2e/test_<feature>.py --headed --slowmo 250
   ```

   `uv run playwright codegen <url>` records clicks into code, which is a quick
   way to find good locators — then move them into a page object.

Need credentials or other settings? Add them to `Settings` in
`src/harness/config.py`, to `.env.example`, and to the README's configuration
table, and read them via the `config` fixture.

## 6. Remove the demo

Once a real test exists, delete `tests/e2e/fixtures/`,
`tests/e2e/pages/example_page.py`, `tests/e2e/test_example.py`, and the
`local_fixture_page` fixture in `tests/e2e/conftest.py`. Run `make check` again.

## 7. Wire up CI

- `ci.yml` already runs on every push and pull request — nothing to do.
- To run against a deployed environment on a schedule, set a repository
  variable `BASE_URL` and see [CI workflows](ci.md#e2e-live-target).
- Turn on Dependabot alerts and security updates in the repository settings;
  `.github/dependabot.yml` already schedules version-update PRs.

## Using an AI coding agent

`AGENTS.md` tells coding agents (Claude Code, Codex, Copilot, Cursor, …) how
this repository works: the commands, where code goes, and the conventions to
keep. `CLAUDE.md` simply imports it. Keep `AGENTS.md` current as you add
conventions of your own — it's the cheapest way to get consistent output from
an agent.
