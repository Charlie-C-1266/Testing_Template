"""Pick optional packages for this harness and add them with uv.

Run it once after creating your repository from the template:

    make packages                                   # interactive menu
    uv run python scripts/add_packages.py --list    # show the catalog
    uv run python scripts/add_packages.py --packages pandas,httpx --yes

Each choice is added with `uv add`, so it lands in `pyproject.toml` and
`uv.lock` (commit both) and is installed into `.venv` straight away — in the dev
container, that's the container's environment. Test-only tooling goes in the
`dev` dependency group; packages your harness code imports go in the main
dependencies. Typing stubs are added alongside packages that need them, so
`mypy --strict` keeps passing.

Playwright is not in the catalog: it's always installed, because the e2e
fixtures, CI, and dev container are built around it.

Standard library only, so it runs before anything else is installed.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Package:
    """One optional package the menu offers."""

    name: str
    """What the user types or passes to `--packages`; also the PyPI name."""
    summary: str
    group: str
    requirement: str = ""
    """What `uv add` receives, when it differs from `name` (e.g. extras)."""
    dev: bool = False
    """Test-only tooling: goes in the `dev` dependency group."""
    stubs: tuple[str, ...] = ()
    """Typing stubs added to the `dev` group so mypy strict stays green."""
    note: str = ""
    """Printed after installing: the one thing to know before using it."""

    @property
    def spec(self) -> str:
        return self.requirement or self.name


CATALOG: tuple[Package, ...] = (
    # ── Data ─────────────────────────────────────────────────────────────────
    Package(
        "pandas", "DataFrames for test data and result checks", "Data", stubs=("pandas-stubs",)
    ),
    Package("polars", "Fast DataFrames, a lighter alternative to pandas", "Data"),
    Package("numpy", "Numeric arrays", "Data"),
    Package("openpyxl", "Read and write Excel files", "Data", stubs=("types-openpyxl",)),
    Package("pyyaml", "Read and write YAML", "Data", stubs=("types-PyYAML",)),
    # ── Models and validation ────────────────────────────────────────────────
    Package("pydantic", "Typed models and validation for API payloads", "Models and validation"),
    Package(
        "pydantic-settings",
        "Typed settings from env vars (an alternative to harness.config)",
        "Models and validation",
    ),
    Package(
        "jsonschema",
        "Validate responses against JSON Schema",
        "Models and validation",
        stubs=("types-jsonschema",),
    ),
    # ── HTTP and APIs ────────────────────────────────────────────────────────
    Package("httpx", "HTTP client, sync and async — for API tests", "HTTP and APIs"),
    Package("requests", "The classic sync HTTP client", "HTTP and APIs", stubs=("types-requests",)),
    Package("respx", "Mock httpx requests in tests", "HTTP and APIs", dev=True),
    # ── Async ────────────────────────────────────────────────────────────────
    Package(
        "pytest-asyncio",
        "Write `async def` tests (asyncio itself is built in)",
        "Async",
        dev=True,
        note="Mark async tests with @pytest.mark.asyncio, or set asyncio_mode = "
        '"auto" under [tool.pytest.ini_options]. Async Playwright needs '
        "playwright.async_api and its own fixtures; the bundled ones are sync.",
    ),
    # ── Test data ────────────────────────────────────────────────────────────
    Package("faker", "Realistic fake names, emails, addresses", "Test data"),
    Package("hypothesis", "Property-based testing", "Test data", dev=True),
    # ── Test tooling ─────────────────────────────────────────────────────────
    Package("pytest-mock", "The `mocker` fixture around unittest.mock", "Test tooling", dev=True),
    Package(
        "pytest-rerunfailures",
        "Retry flaky tests: --reruns 2",
        "Test tooling",
        dev=True,
        note="Use retries to buy time, not to hide flakiness: `--reruns 2` in CI only.",
    ),
    Package("syrupy", "Snapshot testing (the `snapshot` fixture)", "Test tooling", dev=True),
    Package("pytest-html", "Self-contained HTML test report", "Test tooling", dev=True),
    Package(
        "allure-pytest",
        "Allure reports (needs the Allure CLI to view)",
        "Test tooling",
        dev=True,
    ),
    # ── Databases ────────────────────────────────────────────────────────────
    Package("sqlalchemy", "SQL toolkit/ORM for seeding and checking data", "Databases"),
    Package(
        "psycopg",
        "PostgreSQL driver (binary build, no compiler needed)",
        "Databases",
        requirement="psycopg[binary]",
    ),
)

BY_NAME: dict[str, Package] = {package.name: package for package in CATALOG}


def canonical(name: str) -> str:
    """Normalise a distribution name the way PyPI does (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def installed_names(pyproject: Path = PROJECT_ROOT / "pyproject.toml") -> set[str]:
    """Distribution names already declared in `pyproject.toml` (any group)."""
    data = tomllib.loads(pyproject.read_text())
    requirements: list[str] = list(data.get("project", {}).get("dependencies", []))
    for group in data.get("dependency-groups", {}).values():
        requirements.extend(item for item in group if isinstance(item, str))
    return {canonical(re.split(r"[\s\[<>=!~;]", req, maxsplit=1)[0]) for req in requirements}


def parse_selection(raw: str, menu: Sequence[Package]) -> list[Package]:
    """Turn `1 3, pandas` into packages. Numbers index `menu` from 1.

    Raises ValueError naming every token that isn't a menu number or a name.
    """
    chosen: list[Package] = []
    unknown: list[str] = []
    for token in re.split(r"[\s,]+", raw.strip()):
        if not token:
            continue
        if token.isdigit() and 1 <= int(token) <= len(menu):
            package = menu[int(token) - 1]
        elif canonical(token) in BY_NAME:
            package = BY_NAME[canonical(token)]
        else:
            unknown.append(token)
            continue
        if package not in chosen:
            chosen.append(package)
    if unknown:
        raise ValueError(f"not in the menu: {', '.join(unknown)}")
    return chosen


def uv_commands(packages: Iterable[Package]) -> list[list[str]]:
    """The `uv add` invocations that install `packages`: runtime, then dev."""
    runtime: list[str] = []
    dev: list[str] = []
    for package in packages:
        (dev if package.dev else runtime).append(package.spec)
        dev.extend(package.stubs)
    commands = []
    if runtime:
        commands.append(["uv", "add", *runtime])
    if dev:
        commands.append(["uv", "add", "--dev", *dev])
    return commands


def render_menu(menu: Sequence[Package], installed: set[str]) -> str:
    """The numbered, grouped catalog, flagging what's already installed."""
    lines: list[str] = []
    group = ""
    width = max(len(package.name) for package in menu)
    for number, package in enumerate(menu, start=1):
        if package.group != group:
            group = package.group
            lines.append(f"\n  {group}")
        tags = []
        if package.dev:
            tags.append("dev")
        if canonical(package.name) in installed:
            tags.append("installed")
        suffix = f"  [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {number:>3}. {package.name:<{width}}  {package.summary}{suffix}")
    return "\n".join(lines)


def run(
    packages: Sequence[Package],
    *,
    dry_run: bool,
    execute: Callable[[list[str]], int] = lambda cmd: subprocess.call(cmd, cwd=PROJECT_ROOT),
) -> int:
    """Run (or print) the uv commands, then the per-package notes."""
    for command in uv_commands(packages):
        print(f"$ {shlex.join(command)}")
        if not dry_run and (code := execute(command)) != 0:
            print(f"uv exited with {code}; nothing after this step was added.", file=sys.stderr)
            return code
    notes = [f"  {package.name}: {package.note}" for package in packages if package.note]
    if notes:
        print("\nWorth knowing:\n" + "\n".join(notes))
    if not dry_run:
        print("\nDone. Commit pyproject.toml and uv.lock so everyone gets the same set.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--list", action="store_true", help="print the catalog and exit")
    parser.add_argument("--packages", metavar="NAMES", help="comma-separated names; skips the menu")
    parser.add_argument("--yes", "-y", action="store_true", help="don't ask for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="print the uv commands only")
    args = parser.parse_args(argv)

    installed = installed_names()
    print("Playwright, pytest, ruff, and mypy are already included.")
    print(render_menu(CATALOG, installed))
    if args.list:
        return 0

    if args.packages is None:
        if not sys.stdin.isatty():
            print("\nNo terminal to prompt on: pass --packages NAME,NAME.", file=sys.stderr)
            return 2
        raw = input("\nNumbers or names, separated by spaces or commas (Enter to skip): ")
    else:
        raw = args.packages

    try:
        chosen = parse_selection(raw, CATALOG)
    except ValueError as error:
        print(f"\n{error}", file=sys.stderr)
        return 2

    skipped = [package.name for package in chosen if canonical(package.name) in installed]
    chosen = [package for package in chosen if canonical(package.name) not in installed]
    if skipped:
        print(f"\nAlready installed, skipping: {', '.join(skipped)}")
    if not chosen:
        print("\nNothing to add.")
        return 0

    print("\nAbout to run:")
    for command in uv_commands(chosen):
        print(f"  {shlex.join(command)}")
    confirmed = args.yes or args.dry_run
    if not confirmed and input("Proceed? [Y/n] ").strip().lower() not in {"", "y", "yes"}:
        print("Cancelled.")
        return 1
    print()
    return run(chosen, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
