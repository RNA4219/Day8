from __future__ import annotations

import importlib.util
import py_compile
import statistics
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_analyze_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "analyze.py"
    spec = importlib.util.spec_from_file_location("analyze", module_path)
    if spec is None or spec.loader is None:
        pytest.fail("Failed to load analyze.py spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_analyze_script_compiles() -> None:
    script_path = REPO_ROOT / "scripts" / "analyze.py"
    py_compile.compile(str(script_path), doraise=True)


def test_p95_fallback_returns_max_when_quantiles_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    analyze = load_analyze_module()

    def _raise_statistics_error(*_args: object, **_kwargs: object) -> list[float]:
        raise statistics.StatisticsError("forced failure")

    monkeypatch.setattr(analyze.statistics, "quantiles", _raise_statistics_error)

    assert analyze.p95([10, 20]) == 20


def test_p95_fallback_uses_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    analyze = load_analyze_module()

    def _raise_statistics_error(*_args: object, **_kwargs: object) -> list[float]:
        raise statistics.StatisticsError("forced failure")

    monkeypatch.setattr(analyze.statistics, "quantiles", _raise_statistics_error)

    assert analyze.p95([100, 200]) == 200
