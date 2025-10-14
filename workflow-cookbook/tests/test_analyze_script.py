from __future__ import annotations

import importlib.util
import py_compile
import statistics
from pathlib import Path


def test_p95_fallback_rounds_up(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "analyze.py"
    spec = importlib.util.spec_from_file_location("_analyze_test_module", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def _raise_stats_error(*_: object, **__: object) -> list[float]:
        raise statistics.StatisticsError("boom")

    monkeypatch.setattr(module.statistics, "quantiles", _raise_stats_error)

    assert module.p95([10, 20]) == 20


def test_analyze_script_compiles(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "analyze.py"
    cfile = tmp_path / "analyze.pyc"

    compiled_path = py_compile.compile(
        script_path,
        cfile=cfile,
        doraise=True,
    )

    assert Path(compiled_path) == cfile
