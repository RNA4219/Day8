"""Day8 metrics collector for Prometheus and Chainlit logs."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple
import urllib.error
import urllib.request

DEFAULT_PROM_URL = "http://localhost:8000/metrics"
DEFAULT_METRIC_PREFIX = "day8_"
REQUIRED_METRIC_SUFFIXES: list[str] = [
    "app_boot_timestamp",
    "jobs_processed_total",
    "jobs_failed_total",
    "healthz_request_total",
]
_ADDITIVE_SUFFIXES: Tuple[str, ...] = ("_total", "_sum", "_count")
_TIMESTAMP_SUFFIXES: Tuple[str, ...] = ("_timestamp",)
_LABEL_PATTERN = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=\"((?:\\.|[^\"])*)\"")


def _sanitize_label_value_for_suffix(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]", "_", value)


def _required_metric_names(metric_prefix: str) -> list[str]:
    return [f"{metric_prefix}{suffix}" for suffix in REQUIRED_METRIC_SUFFIXES]


def collect_prometheus_metrics(
    url: str,
    metric_prefix: str = DEFAULT_METRIC_PREFIX,
    *,
    timeout: float = 5.0,
) -> Dict[str, float]:
    """Fetch metrics from a Prometheus endpoint and filter by prefix."""
    try:
        response_cm = urllib.request.urlopen(  # type: ignore[no-untyped-call]
            url,
            timeout=timeout,
        )
        with response_cm as response:
            payload = response.read().decode("utf-8")
    except (urllib.error.URLError, OSError) as exc:
        print(
            f"Failed to collect Prometheus metrics from {url}: {exc}",
            file=sys.stderr,
        )
        return {}
    results: Dict[str, float] = {}
    for line in payload.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        normalized_metric = _normalize_prometheus_metric_name(
            parts[0], preserve_label_for_bucket=True
        )
        if not normalized_metric.startswith(metric_prefix):
            continue
        try:
            numeric_value = float(parts[1])
        except ValueError:
            continue
        if not math.isfinite(numeric_value):
            print(
                "Skipping non-finite value for Prometheus metric"
                f" {normalized_metric}: {parts[1]}",
                file=sys.stderr,
            )
            continue
        previous_value = results.get(normalized_metric)
        if previous_value is None:
            results[normalized_metric] = numeric_value
        elif normalized_metric.endswith(_TIMESTAMP_SUFFIXES):
            results[normalized_metric] = max(previous_value, numeric_value)
        elif normalized_metric.endswith(_ADDITIVE_SUFFIXES):
            results[normalized_metric] = previous_value + numeric_value
        else:
            results[normalized_metric] = numeric_value
    return results


def _normalize_prometheus_metric_name(
    metric: str, *, preserve_label_for_bucket: bool = False
) -> str:
    label_start = metric.find("{")
    label_end = metric.find("}", label_start) if label_start != -1 else -1
    labels = metric[label_start : label_end + 1] if label_start != -1 and label_end != -1 else ""

    base = metric
    for delimiter in ("{", "[", "("):
        index = metric.find(delimiter)
        if index != -1:
            base = metric[:index]
            break

    if preserve_label_for_bucket and base.endswith("_bucket") and labels:
        return f"{base}{labels}"

    if not labels:
        return base

    parsed_labels = _LABEL_PATTERN.findall(labels)
    if not parsed_labels:
        return base

    if base.endswith(_ADDITIVE_SUFFIXES) or base.endswith(_TIMESTAMP_SUFFIXES):
        return base

    if base.endswith("_seconds"):
        quantile_value: str | None = None
        remaining_labels: list[tuple[str, str]] = []
        for key, value in parsed_labels:
            if key == "quantile" and quantile_value is None:
                quantile_value = value
            else:
                remaining_labels.append((key, value))
        if quantile_value is not None:
            suffix_value = _sanitize_label_value_for_suffix(quantile_value)
            suffix = f"_quantile_{suffix_value}"
            if remaining_labels:
                formatted_remaining = ",".join(
                    f'{key}="{value}"' for key, value in sorted(remaining_labels)
                )
                return f"{base}{suffix}{{{formatted_remaining}}}"
            return f"{base}{suffix}"

    formatted_labels = ",".join(
        f'{key}="{value}"' for key, value in sorted(parsed_labels)
    )
    return f"{base}{{{formatted_labels}}}"


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
                fallback_record = json.loads(raw_line[start : end + 1])
            except json.JSONDecodeError:
                continue
            if isinstance(fallback_record, Mapping) and not any(
                key in fallback_record for key in ("metric", "name", "metrics")
            ):
                record = {"metrics": fallback_record}
            else:
                record = fallback_record
        for metric, value in _iter_metric_entries(record):
            if not metric.startswith(metric_prefix):
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(numeric):
                print(
                    "Skipping non-finite value for Chainlit metric"
                    f" {metric}: {value}",
                    file=sys.stderr,
                )
                continue
            results[metric] = numeric
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
        for key, value in source.items():
            if key in merged:
                continue
            merged[key] = value
    return merged


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    prom_metrics = collect_prometheus_metrics(args.prom_url, metric_prefix=args.metric_prefix)
    chainlit_metrics: Dict[str, float] = {}
    if args.chainlit_log is not None:
        chainlit_metrics = collect_chainlit_metrics(args.chainlit_log, metric_prefix=args.metric_prefix)

    merged = _merge_metrics(prom_metrics, chainlit_metrics)
    required_metric_names = _required_metric_names(args.metric_prefix)
    missing = [name for name in required_metric_names if name not in merged]

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
