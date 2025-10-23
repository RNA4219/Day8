"""Makefile target behavior tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_HELP_LINES = [
    "printf 'fmt   Format code with ruff format.\\n'",
    "printf 'lint  Run Ruff lint checks.\\n'",
    "printf 'type  Run mypy strict type checks.\\n'",
    "printf 'test  Run pytest suites.\\n'",
    "printf 'check Run lint, type, and test targets.\\n'",
]

EXPECTED_CHECK_LINES = [
    "ruff check .",
    "mypy --strict workflow-cookbook",
    "pytest -q tests workflow-cookbook/tests",
]


def _run_make_target(target: str) -> list[str]:
    completed = subprocess.run(
        ["make", "-n", target],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return completed.stdout.splitlines()


def test_make_help_outputs_expected_lines() -> None:
    output = _run_make_target("help")
    assert output == EXPECTED_HELP_LINES


def test_make_check_runs_expected_commands() -> None:
    output = _run_make_target("check")
    assert output == EXPECTED_CHECK_LINES
