"""Day8 metrics collector for Prometheus and Chainlit logs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple
import urllib.request

DEFAULT_PROM_URL = "http://localhost:8000/metrics"
DEFAULT_METRIC_PREFIX = "day8_"
REQUIRED_METRICS = (
    "day8_app_boot_timestamp",
    "day8_jobs_processed_total",
    "day8_jobs_failed_total",
    "day8_healthz_request_total",
)


def collect_prometheus_metrics(url: str, metric_prefix: str = DEFAULT_METRIC_PREFIX) -> Dict[str, float]:
    """Fetch metrics from a Prometheus endpoint and filter by prefix."""
    with urllib.request.urlopen(url) as response:  # type: ignore[no-untyped-call]
        payload = response.read().decode("utf-8")
    results: Dict[str, float] = {}
    for line in payload.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        metric, value = parts[0], parts[1]
        if not metric.startswith(metric_prefix):
            continue
        try:
            results[metric] = float(value)
        except ValueError:
            continue
    return results


def collect_chainlit_metrics(path: Path, metric_prefix: str = DEFAULT_METRIC_PREFIX) -> Dict[str, float]:
    """Aggregate metrics from Chainlit JSONL logs."""
    if not path.exists():
        return {}
    results: Dict[str, float] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            start = raw_line.find("{")
            end = raw_line.rfind("}")
            if start == -1 or end == -1 or start >= end:
                continue
            try:
                record = json.loads(raw_line[start : end + 1])
            except json.JSONDecodeError:
                continue
        for metric, value in _iter_metric_entries(record):
            if not metric.startswith(metric_prefix):
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            results[metric] = results.get(metric, 0.0) + numeric
    return results


def _iter_metric_entries(record: Any) -> Iterable[Tuple[str, Any]]:
    if not isinstance(record, Mapping):
        return ()

    metric_entries: list[Tuple[str, Any]] = []
    metric_name = record.get("metric")
    if metric_name is not None and "value" in record:
        metric_entries.append((metric_name, record["value"]))

    name = record.get("name")
    if name is not None and "value" in record:
        metric_entries.append((name, record["value"]))

    metrics = record.get("metrics")
    if isinstance(metrics, Mapping):
        metric_entries.extend((key, value) for key, value in metrics.items())

    return metric_entries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect Day8 metrics from Prometheus and Chainlit logs")
    parser.add_argument("--prom-url", default=DEFAULT_PROM_URL, help="Prometheus metrics endpoint URL")
    parser.add_argument(
        "--chainlit-log",
        type=Path,
        default=None,
        help="Path to Chainlit JSONL log file",
    )
    parser.add_argument(
        "--metric-prefix",
        default=DEFAULT_METRIC_PREFIX,
        help="Metric name prefix to filter (default: day8_)",
    )
    parser.add_argument(
        "--output-format",
        choices=("json",),
        default="json",
        help="Output format (currently only json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file path to write metrics output",
    )
    return parser


def _merge_metrics(*sources: Mapping[str, float]) -> Dict[str, float]:
    merged: Dict[str, float] = {}
    for source in sources:
        merged.update(source)
    return merged


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    prom_metrics = collect_prometheus_metrics(args.prom_url, metric_prefix=args.metric_prefix)
    chainlit_metrics: Dict[str, float] = {}
    if args.chainlit_log is not None:
        chainlit_metrics = collect_chainlit_metrics(args.chainlit_log, metric_prefix=args.metric_prefix)

    merged = _merge_metrics(prom_metrics, chainlit_metrics)
    missing = sorted(metric for metric in REQUIRED_METRICS if metric not in merged)

    output = {
        "prometheus": prom_metrics,
        "chainlit": chainlit_metrics,
        "metrics": merged,
    }
    formatted = json.dumps(output, indent=2, sort_keys=True)
    print(formatted)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{formatted}\n", encoding="utf-8")

    if missing:
        print(f"Missing required metrics: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
