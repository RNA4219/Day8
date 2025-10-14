from __future__ import annotations

import importlib.util
import json
import py_compile
import statistics
from importlib.abc import Loader
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_analyze_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "analyze.py"
    spec = importlib.util.spec_from_file_location("analyze", module_path)
    if spec is None or spec.loader is None:
        pytest.fail("Failed to load analyze.py spec")
    loader = spec.loader
    if not isinstance(loader, Loader):
        pytest.fail("analyze.py loader does not support exec_module")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
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


def test_load_results_handles_null_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    analyze = load_analyze_module()
    log_path = tmp_path / "results.jsonl"
    log_path.write_text(
        "\n".join(
            [
                json.dumps({"name": "case-null", "duration_ms": None, "status": "pass"}),
                json.dumps({"name": "case-str", "duration_ms": "7"}),
                json.dumps({"name": "case-int", "duration_ms": 5}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(analyze, "LOG", log_path)

    _tests, durs, _fails = analyze.load_results()

    assert durs
    assert all(isinstance(dur, int) for dur in durs)
    assert durs[0] == 0
    assert durs[1] == 0
    percentile = analyze.p95(durs)
    assert isinstance(percentile, int)
