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
_BUCKET_SUFFIXES: Tuple[str, ...] = ("_bucket",)
_TIMESTAMP_SUFFIXES: Tuple[str, ...] = ("_timestamp",)
_LABEL_PATTERN = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=\"((?:\\.|[^\"\\])*)\"")
_ENVIRONMENT_LABEL_KEYS: frozenset[str] = frozenset(
    {
        "instance",
        "job",
        "pod",
        "pod_name",
        "pod_ip",
        "pod_uid",
        "container",
        "container_id",
        "container_name",
        "node",
        "namespace",
        "service",
        "endpoint",
    }
)


def _sanitize_label_value_for_suffix(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]", "_", value)


def _required_metric_names(metric_prefix: str) -> list[str]:
    return [f"{metric_prefix}{suffix}" for suffix in REQUIRED_METRIC_SUFFIXES]


def _filter_environment_labels(labels: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    filtered_labels: list[tuple[str, str]] = []
    for key, value in labels:
        if key in _ENVIRONMENT_LABEL_KEYS:
            continue
        filtered_labels.append((key, value))
    return filtered_labels


def _is_unescaped_quote(text: str, index: int) -> bool:
    if text[index] != "\"":
        return False
    backslash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslash_count += 1
        cursor -= 1
    return backslash_count % 2 == 0


def _split_prometheus_sample(line: str) -> tuple[str, str, str | None] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    cursor = len(stripped) - 1

    def extract_token(text: str, index: int) -> tuple[str, int] | None:
        cursor_inner = index
        in_quotes = False
        while cursor_inner >= 0 and text[cursor_inner].isspace():
            cursor_inner -= 1
        if cursor_inner < 0:
            return None
        end_pos = cursor_inner
        while cursor_inner >= 0:
            char = text[cursor_inner]
            if char == "\"" and _is_unescaped_quote(text, cursor_inner):
                in_quotes = not in_quotes
                cursor_inner -= 1
                continue
            if not in_quotes and char.isspace():
                break
            cursor_inner -= 1
        start_pos = cursor_inner + 1
        token = text[start_pos : end_pos + 1]
        return token, cursor_inner

    first_token = extract_token(stripped, cursor)
    if first_token is None:
        return None
    last_token, cursor = first_token
    metric_and_value = stripped[: cursor + 1]
    second_token = extract_token(metric_and_value, len(metric_and_value) - 1)
    if second_token is None:
        metric_part = metric_and_value.strip()
        if not metric_part:
            return None
        value_text = last_token
        timestamp_text = None
    else:
        value_candidate, cursor = second_token
        metric_part_text = metric_and_value[: cursor + 1].strip()
        if not metric_part_text:
            metric_part = metric_and_value.strip()
            if not metric_part:
                return None
            value_text = last_token
            timestamp_text = None
        else:
            metric_part = metric_part_text
            value_text = value_candidate
            timestamp_text = last_token
    if not metric_part or not value_text:
        return None
    return metric_part, value_text, timestamp_text


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
        parsed_line = _split_prometheus_sample(line)
        if parsed_line is None:
            continue
        metric_name, value_text, _timestamp_text = parsed_line
        normalized_metric = _normalize_prometheus_metric_name(
            metric_name, preserve_label_for_bucket=True
        )
        if not normalized_metric.startswith(metric_prefix):
            continue
        try:
            numeric_value = float(value_text)
        except ValueError:
            continue
        if not math.isfinite(numeric_value):
            print(
                "Skipping non-finite value for Prometheus metric"
                f" {normalized_metric}: {value_text}",
                file=sys.stderr,
            )
            continue
        previous_value = results.get(normalized_metric)
        metric_base = normalized_metric.split("{", 1)[0]
        if previous_value is None:
            results[normalized_metric] = numeric_value
            continue

        if "_quantile_" in metric_base:
            results[normalized_metric] = max(previous_value, numeric_value)
        elif metric_base.endswith(_TIMESTAMP_SUFFIXES):
            results[normalized_metric] = max(previous_value, numeric_value)
        elif metric_base.endswith(_ADDITIVE_SUFFIXES) or metric_base.endswith(
            _BUCKET_SUFFIXES
        ):
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

    parsed_labels = _LABEL_PATTERN.findall(labels) if labels else []

    if preserve_label_for_bucket and base.endswith("_bucket") and labels:
        if parsed_labels:
            filtered_labels = _filter_environment_labels(parsed_labels)
            if not filtered_labels:
                return base
            formatted_bucket_labels = ",".join(
                f'{key}="{value}"' for key, value in sorted(filtered_labels)
            )
            return f"{base}{{{formatted_bucket_labels}}}"
        return base

    if not labels:
        return base

    if not parsed_labels:
        return base

    quantile_value: str | None = None
    remaining_labels: list[tuple[str, str]] = []
    for key, value in parsed_labels:
        if key == "quantile" and quantile_value is None:
            quantile_value = value
            continue
        remaining_labels.append((key, value))

    filtered_labels = _filter_environment_labels(remaining_labels)

    normalized_base = base
    if quantile_value is not None:
        suffix_value = _sanitize_label_value_for_suffix(quantile_value)
        normalized_base = f"{base}_quantile_{suffix_value}"
    elif base.endswith(_ADDITIVE_SUFFIXES) or base.endswith(_TIMESTAMP_SUFFIXES):
        return base

    if not filtered_labels:
        return normalized_base

    formatted_labels = ",".join(
        f'{key}="{value}"' for key, value in sorted(filtered_labels)
    )
    return f"{normalized_base}{{{formatted_labels}}}"


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
