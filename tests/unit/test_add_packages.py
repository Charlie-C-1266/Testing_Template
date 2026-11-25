"""Unit tests for the optional-package picker (scripts/add_packages.py)."""

from pathlib import Path

import pytest

from scripts import add_packages
from scripts.add_packages import (
    BY_NAME,
    CATALOG,
    installed_names,
    main,
    parse_selection,
    run,
    uv_commands,
)


def test_catalog_names_are_unique_and_exclude_playwright() -> None:
    names = [package.name for package in CATALOG]

    assert len(names) == len(set(names))
    assert "playwright" not in names
    assert "asyncio" not in names  # standard library; pytest-asyncio is the package


def test_selection_accepts_numbers_names_and_mixed_separators() -> None:
    chosen = parse_selection("1, pydantic  1 HTTPX", CATALOG)

    assert [package.name for package in chosen] == [CATALOG[0].name, "pydantic", "httpx"]


def test_selection_rejects_unknown_tokens() -> None:
    with pytest.raises(ValueError, match="99, nope"):
        parse_selection("pandas 99 nope", CATALOG)


def test_blank_selection_is_empty() -> None:
    assert parse_selection("   ", CATALOG) == []


def test_commands_split_runtime_and_dev_and_add_stubs() -> None:
    packages = [BY_NAME["pandas"], BY_NAME["pytest-asyncio"], BY_NAME["psycopg"]]

    assert uv_commands(packages) == [
        ["uv", "add", "pandas", "psycopg[binary]"],
        ["uv", "add", "--dev", "pandas-stubs", "pytest-asyncio"],
    ]


def test_installed_names_reads_every_group(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\ndependencies = ["Pydantic>=2", "psycopg[binary]"]\n'
        "[dependency-groups]\ndev = [\"pytest_asyncio; python_version>'3'\"]\n"
    )

    assert installed_names(pyproject) == {"pydantic", "psycopg", "pytest-asyncio"}


def test_run_stops_at_the_first_failing_command(capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[list[str]] = []

    def fail(command: list[str]) -> int:
        calls.append(command)
        return 1

    code = run([BY_NAME["httpx"], BY_NAME["respx"]], dry_run=False, execute=fail)

    assert code == 1
    assert calls == [["uv", "add", "httpx"]]


def test_dry_run_prints_commands_without_running(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(add_packages, "installed_names", set)

    assert main(["--packages", "faker,hypothesis", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "$ uv add faker" in out
    assert "$ uv add --dev hypothesis" in out


def test_already_installed_packages_are_skipped(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(add_packages, "installed_names", lambda: {"faker"})

    assert main(["--packages", "faker,numpy", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Already installed, skipping: faker" in out
    assert "$ uv add numpy" in out
    assert "uv add faker" not in out


def test_without_a_terminal_the_menu_asks_for_flags(capsys: pytest.CaptureFixture[str]) -> None:
    # pytest captures stdin, so it is never a TTY here.
    assert main([]) == 2
    assert "--packages" in capsys.readouterr().err
