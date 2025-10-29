"""Tests for scripts.perf.collect_metrics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
from urllib.error import URLError

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
    expected_prefix: str = "day8_",
) -> None:
    def fake_collect_prometheus(url: str, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == expected_prefix
        return prom_metrics

    def fake_collect_chainlit(path: Path, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == expected_prefix
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


def test_collect_prometheus_metrics_passes_timeout(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    captured: Dict[str, float | str] = {}

    def fake_urlopen(url: str, *, timeout: float):
        captured["url"] = url
        captured["timeout"] = timeout
        return _DummyResponse(b"day8_jobs_processed_total 7\n")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics",
        timeout=3.0,
    )

    assert captured == {"url": "http://example.test/metrics", "timeout": 3.0}
    assert result == {"day8_jobs_processed_total": 7.0}


def test_collect_prometheus_metrics_supports_labels_with_spaces(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = (
        'day8_jobs_processed_total{job="batch worker",instance="a"} 5\n'
        'day8_jobs_processed_total{job="batch worker",instance="b"} 7\n'
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {"day8_jobs_processed_total": 12.0}


def test_collect_prometheus_metrics_supports_labels_with_spaces_and_timestamp(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = (
        'day8_jobs_processed_total{job="batch worker",instance="a"} 5 1700000000\n'
        'day8_jobs_processed_total{instance="b",job="batch worker"} 7 1700000001\n'
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {"day8_jobs_processed_total": 12.0}


def test_collect_prometheus_metrics_merges_bucket_metrics_with_env_labels(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = "\n".join(
        [
            'day8_latency_bucket{le="0.5",path="/",instance="a"} 1',
            'day8_latency_bucket{le="0.5",path="/",instance="b"} 2',
            'day8_latency_bucket{le="1",path="/",instance="a"} 3',
            'day8_latency_bucket{le="1",path="/",instance="b"} 4',
        ]
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {
        'day8_latency_bucket{le="0.5",path="/"}': 3.0,
        'day8_latency_bucket{le="1",path="/"}': 7.0,
    }


def test_collect_prometheus_metrics_merges_quantile_metrics_with_env_labels(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = "\n".join(
        [
            'day8_latency_seconds{quantile="0.5",instance="a"} 0.2',
            'day8_latency_seconds{quantile="0.5",instance="b"} 0.4',
            'day8_latency_seconds{quantile="0.9",instance="a"} 0.6',
            'day8_latency_seconds{quantile="0.9",instance="b"} 0.8',
        ]
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {
        "day8_latency_seconds_quantile_0.5": 0.4,
        "day8_latency_seconds_quantile_0.9": 0.8,
    }


def test_collect_prometheus_metrics_merges_quantile_metrics_across_units_and_instances(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = "\n".join(
        [
            'day8_latency_milliseconds{quantile="0.5",instance="a"} 180',
            'day8_latency_milliseconds{quantile="0.5",instance="b"} 220',
            'day8_latency_milliseconds{quantile="0.95",instance="a"} 350',
            'day8_latency_milliseconds{quantile="0.95",instance="b"} 300',
        ]
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {
        "day8_latency_milliseconds_quantile_0.5": 220.0,
        "day8_latency_milliseconds_quantile_0.95": 350.0,
    }


def test_collect_prometheus_metrics_keeps_highest_quantile_value(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = "\n".join(
        [
            'day8_latency_seconds{quantile="0.5",instance="a"} 0.6',
            'day8_latency_seconds{quantile="0.5",instance="b"} 0.2',
        ]
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {"day8_latency_seconds_quantile_0.5": 0.6}


def test_collect_prometheus_metrics_keeps_highest_quantile_value_with_additional_labels(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = "\n".join(
        [
            'day8_latency_seconds{quantile="0.5",status="ok",instance="a"} 0.9',
            'day8_latency_seconds{quantile="0.5",status="ok",instance="b"} 0.3',
        ]
    ).encode("utf-8")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        lambda url, timeout=5.0: _DummyResponse(payload),
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://example.test/metrics"
    )

    assert result == {'day8_latency_seconds_quantile_0.5{status="ok"}': 0.9}


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


def test_main_prefers_prometheus_metrics_over_chainlit_when_conflicting(
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
        "day8_jobs_processed_total": 10.0,
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
        "metrics": {
            "day8_app_boot_timestamp": 1.0,
            "day8_jobs_processed_total": 5.0,
            "day8_jobs_failed_total": 2.0,
            "day8_healthz_request_total": 3.0,
        },
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


@pytest.mark.parametrize(
    "prom_metrics, chainlit_metrics, expected",
    [
        (
            {"day8_jobs_processed_total": 5.0},
            {"day8_jobs_processed_total": 8.0, "day8_jobs_failed_total": 2.0},
            {"day8_jobs_processed_total": 5.0, "day8_jobs_failed_total": 2.0},
        ),
        (
            {"day8_jobs_processed_total": 5.0},
            {"day8_healthz_request_total": 3.0},
            {"day8_jobs_processed_total": 5.0, "day8_healthz_request_total": 3.0},
        ),
        (
            {},
            {"day8_jobs_processed_total": 1.0},
            {"day8_jobs_processed_total": 1.0},
        ),
    ],
)
def test_merge_metrics_prefers_first_source_values(
    collect_metrics_module,
    prom_metrics: Dict[str, float],
    chainlit_metrics: Dict[str, float],
    expected: Dict[str, float],
) -> None:
    merged = collect_metrics_module._merge_metrics(prom_metrics, chainlit_metrics)
    assert merged == expected


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


def test_collect_prometheus_metrics_handles_url_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    error = URLError("network unreachable")

    def fake_urlopen(url: str, timeout: float | None = None):
        raise error

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )
    assert result == {}

    captured = capsys.readouterr()
    assert (
        "Failed to collect Prometheus metrics from http://localhost:8000/metrics"
        in captured.err
    )
    assert captured.out == ""

    chainlit_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_processed_total": 2.0,
        "day8_jobs_failed_total": 3.0,
        "day8_healthz_request_total": 4.0,
    }

    def fake_collect_chainlit(path: Path, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == "day8_"
        return chainlit_metrics

    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        fake_collect_chainlit,
    )

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    assert (
        "Failed to collect Prometheus metrics from http://localhost:8000/metrics"
        in captured.err
    )

    payload = json.loads(captured.out)
    assert payload == {
        "prometheus": {},
        "chainlit": chainlit_metrics,
        "metrics": chainlit_metrics,
    }


def test_main_succeeds_when_prometheus_unreachable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    chainlit_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_processed_total": 2.0,
        "day8_jobs_failed_total": 3.0,
        "day8_healthz_request_total": 4.0,
    }

    def failing_urlopen(url: str, /, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise URLError("unreachable")

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        failing_urlopen,
    )
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": chainlit_metrics,
    )

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "prometheus": {},
        "chainlit": chainlit_metrics,
        "metrics": chainlit_metrics,
    }
    assert "Failed to collect Prometheus metrics" in captured.err


def test_collect_chainlit_metrics_parses_info_metrics_line(
    collect_metrics_module, tmp_path: Path
) -> None:
    log_path = tmp_path / "chainlit.log"
    log_path.write_text(
        "INFO metrics={\"day8_jobs_processed_total\": 2, \"day8_jobs_failed_total\": 1}\n",
        encoding="utf-8",
    )

    metrics = collect_metrics_module.collect_chainlit_metrics(log_path)

    assert metrics == {
        "day8_jobs_processed_total": 2.0,
        "day8_jobs_failed_total": 1.0,
    }


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

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    result = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")
    assert result == {"day8_app_boot_timestamp": pytest.approx(1.6988007e09)}


def test_collect_prometheus_metrics_strips_labels(monkeypatch: pytest.MonkeyPatch, collect_metrics_module) -> None:
    payload = (
        b"day8_jobs_processed_total{instance=\"api\"} 1\n"
        b"day8_jobs_processed_total{instance=\"worker\"} 2\n"
        b"day8_jobs_failed_total 3\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    result = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")

    assert result == {
        "day8_jobs_processed_total": pytest.approx(3.0),
        "day8_jobs_failed_total": pytest.approx(3.0),
    }


def test_collect_prometheus_metrics_preserves_escaped_labels(
    monkeypatch: pytest.MonkeyPatch, collect_metrics_module
) -> None:
    payload = (
        b'day8_request_inflight{path="\\"/api\\"",bucket="p\\n"} 1\n'
        b'day8_request_inflight{bucket="p\\n",path="\\"/api\\""} 2\n'
        b'day8_request_duration_seconds_bucket{path="\\"/api\\"",le="0.5",bucket="p\\n"} 3\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(
        collect_metrics_module.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    assert result[
        'day8_request_inflight{bucket="p\\n",path="\\"/api\\""}'
    ] == pytest.approx(2.0)
    assert result[
        'day8_request_duration_seconds_bucket{bucket="p\\n",le="0.5",path="\\"/api\\""}'
    ] == pytest.approx(3.0)


def test_collect_prometheus_metrics_sorts_bucket_labels(
    monkeypatch: pytest.MonkeyPatch, collect_metrics_module
) -> None:
    payload = (
        b'day8_request_duration_seconds_bucket{le="0.5",path="/api"} 3\n'
        b'day8_request_duration_seconds_bucket{path="/api",le="0.5"} 5\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    expected_key = 'day8_request_duration_seconds_bucket{le="0.5",path="/api"}'
    assert list(result.keys()) == [expected_key]
    assert result[expected_key] == pytest.approx(8.0)


def test_collect_prometheus_metrics_aggregates_bucket_series_from_multiple_pods(
    monkeypatch: pytest.MonkeyPatch, collect_metrics_module
) -> None:
    payload = (
        b'day8_request_duration_seconds_bucket{le="0.5",path="/api"} 3\n'
        b'day8_request_duration_seconds_bucket{path="/api",le="0.5"} 2\n'
        b'day8_request_duration_seconds_bucket{le="1.0",path="/api"} 4\n'
        b'day8_request_duration_seconds_bucket{path="/api",le="1.0"} 1\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    assert result == {
        'day8_request_duration_seconds_bucket{le="0.5",path="/api"}': pytest.approx(5.0),
        'day8_request_duration_seconds_bucket{le="1.0",path="/api"}': pytest.approx(5.0),
    }


def test_collect_prometheus_metrics_sums_duplicate_bucket_samples(
    monkeypatch: pytest.MonkeyPatch, collect_metrics_module
) -> None:
    payload = (
        b'day8_request_duration_seconds_bucket{le="0.5",path="/healthz"} 1\n'
        b'day8_request_duration_seconds_bucket{path="/healthz",le="0.5"} 2\n'
        b'day8_request_duration_seconds_bucket{le="1.0",path="/healthz"} 3\n'
        b'day8_request_duration_seconds_bucket{path="/healthz",le="1.0"} 4\n'
        b'day8_request_duration_seconds_bucket{path="/healthz",le="1.0"} 8\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    assert result == {
        'day8_request_duration_seconds_bucket{le="0.5",path="/healthz"}': pytest.approx(3.0),
        'day8_request_duration_seconds_bucket{le="1.0",path="/healthz"}': pytest.approx(15.0),
    }


def test_main_supports_custom_metric_prefix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"custom_app_boot_timestamp 1\n"
        b"custom_jobs_processed_total 5\n"
        b"custom_jobs_failed_total 2\n"
        b"custom_healthz_request_total 3\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    def fake_collect_chainlit(path: Path, metric_prefix: str = "day8_") -> Dict[str, float]:
        assert metric_prefix == "custom_"
        return {}

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        fake_collect_chainlit,
    )

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics",
        metric_prefix="custom_",
    )
    expected_prom_metrics = {
        "custom_app_boot_timestamp": pytest.approx(1.0),
        "custom_jobs_processed_total": pytest.approx(5.0),
        "custom_jobs_failed_total": pytest.approx(2.0),
        "custom_healthz_request_total": pytest.approx(3.0),
    }
    assert result == expected_prom_metrics

    exit_code = collect_metrics_module.main(
        _prepare_args(tmp_path, ["--metric-prefix", "custom_"])
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": expected_prom_metrics,
        "chainlit": {},
        "metrics": expected_prom_metrics,
    }
    assert captured.err == ""


def test_main_supports_custom_metric_prefix_with_collectors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {
        "custom_app_boot_timestamp": 1.0,
        "custom_jobs_processed_total": 5.0,
    }
    chainlit_metrics: Dict[str, float] = {
        "custom_jobs_failed_total": 2.0,
        "custom_healthz_request_total": 3.0,
    }

    _configure_collectors(
        monkeypatch,
        collect_metrics_module,
        prom_metrics,
        chainlit_metrics,
        expected_prefix="custom_",
    )

    exit_code = collect_metrics_module.main(
        _prepare_args(tmp_path, ["--metric-prefix", "custom_"])
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    expected = {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": {**prom_metrics, **chainlit_metrics},
    }
    assert payload_json == expected
    assert captured.err == ""


def test_collect_prometheus_metrics_aggregates_labeled_series(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_jobs_processed_total{job=\"worker\"} 3\n"
        b"day8_jobs_processed_total{job=\"scheduler\"} 4\n"
        b"day8_jobs_failed_total{job=\"worker\"} 1\n"
        b"day8_healthz_request_total{endpoint=\"/healthz\"} 2\n"
        b"day8_app_boot_timestamp{job=\"worker\"} 1\n"
        b"day8_app_boot_timestamp{job=\"scheduler\"} 5\n"
        b"other_metric 5\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    metrics = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")
    assert metrics == {
        "day8_jobs_processed_total": pytest.approx(7.0),
        "day8_jobs_failed_total": pytest.approx(1.0),
        "day8_healthz_request_total": pytest.approx(2.0),
        "day8_app_boot_timestamp": pytest.approx(5.0),
    }

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": metrics,
        "chainlit": {},
        "metrics": metrics,
    }
    assert captured.err == ""


def test_collect_prometheus_metrics_preserves_quantile_labels(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_latency_seconds{quantile=\"0.5\"} 1.5\n"
        b"day8_latency_seconds{quantile=\"0.9\"} 2.5\n"
        b"day8_jobs_processed_total 5\n"
        b"day8_jobs_failed_total 1\n"
        b"day8_healthz_request_total 3\n"
        b"day8_app_boot_timestamp 100\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    metrics = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")

    assert metrics["day8_latency_seconds_quantile_0.5"] == pytest.approx(1.5)
    assert metrics["day8_latency_seconds_quantile_0.9"] == pytest.approx(2.5)

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": metrics,
        "chainlit": {},
        "metrics": metrics,
    }
    assert captured.err == ""


def test_collect_prometheus_metrics_aggregates_quantiles_with_environment_labels(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = (
        b'day8_latency_seconds{quantile="0.5",instance="api",job="worker"} 1.5\n'
        b'day8_latency_seconds{instance="worker",quantile="0.5",job="scheduler"} 2.0\n'
        b'day8_latency_seconds{job="worker",quantile="0.9",instance="api"} 3.5\n'
        b'day8_latency_seconds{quantile="0.9",job="scheduler",instance="worker"} 4.0\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    assert result == {
        "day8_latency_seconds_quantile_0.5": pytest.approx(2.0),
        "day8_latency_seconds_quantile_0.9": pytest.approx(4.0),
    }


def test_collect_prometheus_metrics_aggregates_quantiles_without_seconds_suffix(
    monkeypatch: pytest.MonkeyPatch,
    collect_metrics_module,
) -> None:
    payload = (
        b'day8_latency_milliseconds{quantile="0.5",instance="a"} 12\n'
        b'day8_latency_milliseconds{instance="b",quantile="0.5"} 18\n'
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)

    result = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )

    assert result == {
        "day8_latency_milliseconds_quantile_0.5": pytest.approx(18.0),
    }


def test_main_preserves_quantile_metric_keys(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_latency_seconds{quantile=\"0.5\"} 1.5\n"
        b"day8_latency_seconds{quantile=\"0.9\"} 2.5\n"
        b"day8_jobs_processed_total 5\n"
        b"day8_jobs_failed_total 1\n"
        b"day8_healthz_request_total 3\n"
        b"day8_app_boot_timestamp 100\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)

    assert payload_json["prometheus"]["day8_latency_seconds_quantile_0.5"] == pytest.approx(1.5)
    assert payload_json["prometheus"]["day8_latency_seconds_quantile_0.9"] == pytest.approx(2.5)
    assert payload_json["metrics"]["day8_latency_seconds_quantile_0.5"] == pytest.approx(1.5)
    assert payload_json["metrics"]["day8_latency_seconds_quantile_0.9"] == pytest.approx(2.5)
    assert captured.err == ""


def test_collect_prometheus_metrics_aggregates_duplicate_series_and_main_uses_totals(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_jobs_processed_total{job=\"worker\"} 3\n"
        b"day8_jobs_processed_total{job=\"scheduler\"} 2\n"
        b"day8_app_boot_timestamp{job=\"worker\"} 100\n"
        b"day8_app_boot_timestamp{job=\"scheduler\"} 200\n"
        b"day8_jobs_failed_total 1\n"
        b"day8_healthz_request_total 4\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    metrics = collect_metrics_module.collect_prometheus_metrics("http://localhost:8000/metrics")
    assert metrics == {
        "day8_jobs_processed_total": pytest.approx(5.0),
        "day8_app_boot_timestamp": pytest.approx(200.0),
        "day8_jobs_failed_total": pytest.approx(1.0),
        "day8_healthz_request_total": pytest.approx(4.0),
    }

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": {
            "day8_jobs_processed_total": pytest.approx(5.0),
            "day8_app_boot_timestamp": pytest.approx(200.0),
            "day8_jobs_failed_total": pytest.approx(1.0),
            "day8_healthz_request_total": pytest.approx(4.0),
        },
        "chainlit": {},
        "metrics": {
            "day8_jobs_processed_total": pytest.approx(5.0),
            "day8_app_boot_timestamp": pytest.approx(200.0),
            "day8_jobs_failed_total": pytest.approx(1.0),
            "day8_healthz_request_total": pytest.approx(4.0),
        },
    }
    assert captured.err == ""


def test_main_aggregates_timestamp_with_max(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_jobs_processed_total{job=\"worker\"} 3\n"
        b"day8_jobs_processed_total{job=\"scheduler\"} 4\n"
        b"day8_app_boot_timestamp{job=\"worker\"} 1\n"
        b"day8_app_boot_timestamp{job=\"scheduler\"} 5\n"
        b"day8_jobs_failed_total 2\n"
        b"day8_healthz_request_total 3\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": {
            "day8_jobs_processed_total": pytest.approx(7.0),
            "day8_app_boot_timestamp": pytest.approx(5.0),
            "day8_jobs_failed_total": pytest.approx(2.0),
            "day8_healthz_request_total": pytest.approx(3.0),
        },
        "chainlit": {},
        "metrics": {
            "day8_jobs_processed_total": pytest.approx(7.0),
            "day8_app_boot_timestamp": pytest.approx(5.0),
            "day8_jobs_failed_total": pytest.approx(2.0),
            "day8_healthz_request_total": pytest.approx(3.0),
        },
    }
    assert captured.err == ""


def test_collect_prometheus_metrics_preserves_histogram_buckets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_latency_seconds_bucket{le=\"0.5\"} 3\n"
        b"day8_latency_seconds_bucket{le=\"1.0\"} 7\n"
        b"day8_latency_seconds_bucket{le=\"+Inf\"} 9\n"
        b"day8_latency_seconds_count 9\n"
        b"day8_latency_seconds_sum 12\n"
        b"day8_jobs_processed_total 5\n"
        b"day8_jobs_failed_total 2\n"
        b"day8_healthz_request_total 3\n"
        b"day8_app_boot_timestamp 1\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    metrics = collect_metrics_module.collect_prometheus_metrics(
        "http://localhost:8000/metrics"
    )
    expected_prom_metrics = {
        'day8_latency_seconds_bucket{le="0.5"}': pytest.approx(3.0),
        'day8_latency_seconds_bucket{le="1.0"}': pytest.approx(7.0),
        'day8_latency_seconds_bucket{le="+Inf"}': pytest.approx(9.0),
        "day8_latency_seconds_count": pytest.approx(9.0),
        "day8_latency_seconds_sum": pytest.approx(12.0),
        "day8_jobs_processed_total": pytest.approx(5.0),
        "day8_jobs_failed_total": pytest.approx(2.0),
        "day8_healthz_request_total": pytest.approx(3.0),
        "day8_app_boot_timestamp": pytest.approx(1.0),
    }
    assert metrics == expected_prom_metrics

    exit_code = collect_metrics_module.main(_prepare_args(tmp_path))
    assert exit_code == 0

    captured = capsys.readouterr()
    payload_json = json.loads(captured.out)
    assert payload_json == {
        "prometheus": metrics,
        "chainlit": {},
        "metrics": metrics,
    }
    assert captured.err == ""


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


def test_collect_chainlit_metrics_keeps_latest_value(tmp_path: Path, collect_metrics_module) -> None:
    log_path = tmp_path / "chainlit.jsonl"
    entries = [
        {"metric": "day8_jobs_processed_total", "value": 3},
        {"metric": "day8_jobs_processed_total", "value": 4},
        {"metric": "day8_jobs_processed_total", "value": 5},
    ]
    log_path.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")

    result = collect_metrics_module.collect_chainlit_metrics(log_path)

    assert result == {"day8_jobs_processed_total": pytest.approx(5.0)}


def test_collect_chainlit_metrics_keeps_latest_value_from_metrics_map(
    tmp_path: Path, collect_metrics_module
) -> None:
    log_path = tmp_path / "chainlit.jsonl"
    entries = [
        {"metrics": {"day8_jobs_failed_total": 1}},
        {"metrics": {"day8_jobs_failed_total": 2}},
        {"metrics": {"day8_jobs_failed_total": 3}},
    ]
    log_path.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")

    result = collect_metrics_module.collect_chainlit_metrics(log_path)

    assert result == {"day8_jobs_failed_total": pytest.approx(3.0)}


def test_collect_chainlit_metrics_extracts_embedded_json(tmp_path: Path, collect_metrics_module) -> None:
    log_path = tmp_path / "chainlit.jsonl"
    log_path.write_text(
        (
            "INFO metrics={"
            "\"metrics\": {\"day8_jobs_processed_total\": 3, \"day8_jobs_failed_total\": 1, \"other\": 5}}"
        )
    )

    result = collect_metrics_module.collect_chainlit_metrics(log_path)
    assert result == {
        "day8_jobs_processed_total": pytest.approx(3.0),
        "day8_jobs_failed_total": pytest.approx(1.0),
    }


def test_main_reports_missing_metric_when_prometheus_returns_nan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    payload = (
        b"day8_app_boot_timestamp NaN\n"
        b"day8_jobs_processed_total 5\n"
        b"day8_jobs_failed_total 2\n"
        b"day8_healthz_request_total 3\n"
    )

    def fake_urlopen(url: str, *, timeout: float = 5.0):  # type: ignore[no-untyped-def]
        return _DummyResponse(payload)

    monkeypatch.setattr(collect_metrics_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        collect_metrics_module,
        "collect_chainlit_metrics",
        lambda path, metric_prefix="day8_": {},
    )

    with pytest.raises(SystemExit) as exc_info:
        collect_metrics_module.main(_prepare_args(tmp_path))

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Skipping non-finite value for Prometheus metric day8_app_boot_timestamp" in captured.err
    assert "Missing required metrics" in captured.err

    payload_json = json.loads(captured.out)
    assert "day8_app_boot_timestamp" not in payload_json["metrics"]
    assert json.loads(captured.out) == payload_json


def test_main_reports_missing_metric_when_chainlit_logs_nan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collect_metrics_module,
) -> None:
    prom_metrics: Dict[str, float] = {
        "day8_app_boot_timestamp": 1.0,
        "day8_jobs_failed_total": 2.0,
        "day8_healthz_request_total": 3.0,
    }

    monkeypatch.setattr(
        collect_metrics_module,
        "collect_prometheus_metrics",
        lambda url, metric_prefix="day8_": prom_metrics,
    )

    args = _prepare_args(tmp_path)
    log_path = Path(args[args.index("--chainlit-log") + 1])
    log_path.write_text(
        json.dumps({"metric": "day8_jobs_processed_total", "value": "NaN"}),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc_info:
        collect_metrics_module.main(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Skipping non-finite value for Chainlit metric day8_jobs_processed_total" in captured.err
    assert "Missing required metrics" in captured.err

    payload_json = json.loads(captured.out)
    assert "day8_jobs_processed_total" not in payload_json["metrics"]
    assert json.loads(captured.out) == payload_json
