"""Tests for scripts.perf.collect_metrics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest

import importlib.util
import sys


MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "perf" / "collect_metrics.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scripts.perf.collect_metrics", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load collect_metrics module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.perf.collect_metrics", module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def collect_metrics_module():
    return _load_module()


class _DummyResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def read(self) -> bytes:
        return self._payload


def _configure_collectors(
    monkeypatch: pytest.MonkeyPatch,
    module,
    prom_metrics: Dict[str, float],
    chainlit_metrics: Dict[str, float],
) -> None:
    def fake_collect_prometheus(url: str, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == "day8_"
        return prom_metrics

    def fake_collect_chainlit(path: Path, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == "day8_"
        return chainlit_metrics

    monkeypatch.setattr(module, "collect_prometheus_metrics", fake_collect_prometheus)
    monkeypatch.setattr(module, "collect_chainlit_metrics", fake_collect_chainlit)


def _prepare_args(tmp_path: Path, extra_args: List[str] | None = None) -> List[str]:
    log_path = tmp_path / "chainlit.jsonl"
    log_path.write_text("")
    args: List[str] = [
        "--prom-url",
        "http://localhost:8000/metrics",
        "--chainlit-log",
        str(log_path),
    ]
    if extra_args:
        args.extend(extra_args)
    return args


def test_main_succeeds_with_required_metrics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_processed_total": 5.0,
    }
    chainlit_metrics: Dict[str, float] = {
        "day8_jobs_failed_total": 2.0,
        "day8_healthz_request_total": 3.0,
    }

    _configure_collectors(monkeypatch, collect_metrics_module, prom_metrics, chainlit_metrics)

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }


def test_main_fails_when_required_metric_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {"day8_app_boot_timestamp": 1.0}
    chainlit_metrics: Dict[str, float] = {}

    _configure_collectors(monkeypatch, collect_metrics_module, prom_metrics, chainlit_metrics)

    with pytest.raises(SystemExit) as exc_info:
        collect_metrics_module.main(_prepare_args(tmp_path))

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Missing required metrics" in captured.err
    payload = json.loads(captured.out)
    assert payload == {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }


def test_main_writes_output_file_when_missing_metric(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {"day8_app_boot_timestamp": 1.0}
    chainlit_metrics: Dict[str, float] = {}

    _configure_collectors(monkeypatch, collect_metrics_module, prom_metrics, chainlit_metrics)

    output_path = tmp_path / "metrics.json"

    with pytest.raises(SystemExit) as exc_info:
        collect_metrics_module.main(
            _prepare_args(tmp_path, ["--output", str(output_path)])
        )

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Missing required metrics" in captured.err
    payload = json.loads(captured.out)
    expected = {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }
    assert payload == expected
    assert json.loads(output_path.read_text()) == expected


def test_main_writes_output_file_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_processed_total": 5.0,
    }
    chainlit_metrics: Dict[str, float] = {
        "day8_jobs_failed_total": 2.0,
        "day8_healthz_request_total": 3.0,
    }

    _configure_collectors(monkeypatch, collect_metrics_module, prom_metrics, chainlit_metrics)

    output_path = tmp_path / "metrics.json"

    exit_code = collect_metrics_module.main(
        _prepare_args(tmp_path, ["--output", str(output_path)])
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    expected = {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }
    assert payload == expected
    assert json.loads(output_path.read_text()) == expected


def test_main_creates_missing_output_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_processed_total": 5.0,
    }
    chainlit_metrics: Dict[str, float] = {
        "day8_jobs_failed_total": 2.0,
        "day8_healthz_request_total": 3.0,
    }

    _configure_collectors(monkeypatch, collect_metrics_module, prom_metrics, chainlit_metrics)

    output_path = tmp_path / "nested" / "metrics.json"

    exit_code = collect_metrics_module.main(
        _prepare_args(tmp_path, ["--output", str(output_path)])
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    expected = {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }
    assert payload == expected
    assert json.loads(output_path.read_text()) == expected


def test_collect_prometheus_metrics_filters_day8_prefix(monkeypatch: pytest.MonkeyPatch, collect_metrics_module) -> None:
    payload = b"""# HELP day8_app_boot_timestamp App boot time\n# TYPE day8_app_boot_timestamp gauge\nday8_app_boot_timestamp 1.6988007e+09\n# TYPE other_metric counter\nother_metric 5\n"""

    def fake_urlopen(url: str):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    result = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")
    assert result == {"day8_app_boot_timestamp": pytest.approx(1.6988007e09)}


def test_collect_chainlit_metrics_supports_multiple_shapes(tmp_path: Path, collect_metrics_module) -> None:
    log_path = tmp_path / "chainlit.jsonl"
    lines = [
        {"metric": "day8_jobs_processed_total", "value": 42},
        {"metrics": {"day8_jobs_failed_total": 2, "other_metric": 3}},
        {"name": "day8_healthz_request_total", "value": 7},
        {"metric": "unrelated", "value": 1},
        "{not-json}",
    ]
    log_path.write_text("\n".join(json.dumps(line) if isinstance(line, dict) else str(line) for line in lines))

    result = collect_metrics_module.collect_chainlit_metrics(log_path)
    assert result == {
        "day8_jobs_processed_total": pytest.approx(42.0),
        "day8_jobs_failed_total": pytest.approx(2.0),
        "day8_healthz_request_total": pytest.approx(7.0),
    }
