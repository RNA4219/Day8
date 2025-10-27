"""Tests for workflow-cookbook.scripts.run_ci_tests."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_run_ci_tests():
    module_name = "workflow_cookbook.scripts.run_ci_tests"
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "run_ci_tests.py"

    package = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("workflow_cookbook", loader=None)
    )
    package.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("workflow_cookbook", package)

    scripts_package = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("workflow_cookbook.scripts", loader=None)
    )
    scripts_package.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("workflow_cookbook.scripts", scripts_package)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load run_ci_tests module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    scripts_package.run_ci_tests = module  # type: ignore[attr-defined]
    return module


run_ci_tests = _load_run_ci_tests()


@pytest.mark.parametrize(
    ("mode", "runner_name", "had_failures", "expected_exit"),
    [
        ("node", "run_node", False, 0),
        ("node", "run_node", True, 1),
        ("python", "run_python", False, 0),
        ("python", "run_python", True, 1),
    ],
)
def test_main_returns_exit_code_based_on_failures(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    runner_name: str,
    had_failures: bool,
    expected_exit: int,
) -> None:
    recorded = {}

    def fake_parse_args() -> SimpleNamespace:
        return SimpleNamespace(mode=mode, reset_log=False)

    def fake_write_output(value: bool) -> None:
        recorded["had_failures"] = value

    monkeypatch.setattr(run_ci_tests, "parse_args", fake_parse_args)
    monkeypatch.setattr(run_ci_tests, "ensure_log", lambda reset: None)
    monkeypatch.setattr(run_ci_tests, runner_name, lambda: had_failures)
    monkeypatch.setattr(run_ci_tests, "write_output", fake_write_output)

    exit_code = run_ci_tests.main()

    assert type(exit_code) is int  # noqa: E721
    assert exit_code == expected_exit
    assert recorded["had_failures"] is had_failures
