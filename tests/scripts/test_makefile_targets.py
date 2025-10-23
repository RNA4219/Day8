"""Makefile target behavior tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_make_target(target: str) -> str:
    completed = subprocess.run(
        ["make", "-n", target],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_make_help_lists_primary_targets() -> None:
    output = _run_make_target("help")
    for target in ("fmt", "lint", "type", "test", "check"):
        assert target in output, f"missing {target!r} in help output"


def test_make_check_runs_expected_commands() -> None:
    output = _run_make_target("check")
    expected_commands = [
        "ruff check .",
        "mypy --strict workflow-cookbook",
        "pytest -q tests workflow-cookbook/tests",
    ]
    for command in expected_commands:
        assert command in output.splitlines()
