from __future__ import annotations

import datetime
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Final

StatusMap = dict[str, set[str]]

WORKFLOW_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
BASE_DIR: Final[Path] = WORKFLOW_ROOT
LOG: Final[Path] = WORKFLOW_ROOT / "logs" / "test.jsonl"
DEFAULT_REPORT: Final[Path] = WORKFLOW_ROOT / "reports" / "today.md"
REPORT: Final[Path] = DEFAULT_REPORT
ISSUE_OUT: Final[Path] = WORKFLOW_ROOT / "reports" / "issue_suggestions.md"
REFLECTION_MANIFEST: Final[Path] = WORKFLOW_ROOT / "reflection.yaml"


def _coerce_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    return None


def _fallback_read_section_value(text: str, section: str, key: str) -> str | None:
    in_section = False
    section_indent = 0
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if stripped.startswith(f"{section}:") and indent == 0:
            in_section = True
            section_indent = indent
            continue
        if indent <= section_indent:
            in_section = False
        if in_section and stripped.startswith(f"{key}:"):
            value = stripped.split(":", 1)[1].split("#", 1)[0].strip()
            if value.startswith(("'", '"')) and value.endswith(value[0]) and len(value) >= 2:
                value = value[1:-1]
            return value or None
    return None


def _fallback_read_section_bool(
    text: str, section: str, key: str, default: bool
) -> bool:
    value = _fallback_read_section_value(text, section, key)
    if value is None:
        return default
    coerced = _coerce_bool(value)
    return coerced if coerced is not None else default


def _fallback_read_suggest_issues(text: str, default: bool) -> bool:
    return _fallback_read_section_bool(text, "actions", "suggest_issues", default)


def _fallback_read_include_why(text: str, default: bool) -> bool:
    return _fallback_read_section_bool(text, "report", "include_why_why", default)


def _fallback_manifest_from_text(
    text: str,
    *,
    default_suggest_issues: bool,
    default_include_why: bool,
) -> dict[str, Any]:
    report_config: dict[str, Any] = {
        "include_why_why": _fallback_read_include_why(text, default_include_why)
    }
    output = _fallback_read_section_value(text, "report", "output")
    if output:
        report_config["output"] = output
    return {
        "actions": {
            "suggest_issues": _fallback_read_suggest_issues(text, default_suggest_issues)
        },
        "report": report_config,
    }


def load_reflection_manifest(
    path: Path | None = None,
    *,
    default_suggest_issues: bool = True,
    default_include_why: bool = True,
) -> dict[str, Any]:
    target = path or REFLECTION_MANIFEST
    if not target.exists():
        return {}
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return _fallback_manifest_from_text(
            text,
            default_suggest_issues=default_suggest_issues,
            default_include_why=default_include_why,
        )
    try:
        loaded = yaml.safe_load(text)
    except Exception:
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def load_actions_suggest_issues(
    path: Path | None = None,
    default: bool = True,
    *,
    manifest: dict[str, Any] | None = None,
) -> bool:
    manifest_data = (
        load_reflection_manifest(
            path,
            default_suggest_issues=default,
            default_include_why=True,
        )
        if manifest is None
        else manifest
    )
    if not manifest_data:
        return default
    actions: Any = manifest_data.get("actions")
    if isinstance(actions, dict):
        suggest = actions.get("suggest_issues")
        coerced = _coerce_bool(suggest)
        if coerced is not None:
            return coerced
    return default


def load_report_include_why(
    path: Path | None = None,
    default: bool = True,
    *,
    manifest: dict[str, Any] | None = None,
) -> bool:
    manifest_data = (
        load_reflection_manifest(
            path,
            default_suggest_issues=True,
            default_include_why=default,
        )
        if manifest is None
        else manifest
    )
    if not manifest_data:
        return default
    report: Any = manifest_data.get("report")
    if isinstance(report, dict):
        include = report.get("include_why_why")
        coerced = _coerce_bool(include)
        if coerced is not None:
            return coerced
    return default


def load_report_output_path(
    path: Path | None = None,
    *,
    default: Path | None = None,
    manifest: dict[str, Any] | None = None,
) -> Path:
    manifest_data = (
        load_reflection_manifest(
            path,
            default_suggest_issues=True,
            default_include_why=True,
        )
        if manifest is None
        else manifest
    )
    fallback = default or REPORT
    report_section: Any = manifest_data.get("report") if manifest_data else None
    candidate: object = report_section.get("output") if isinstance(report_section, dict) else None
    candidate_path: Path | None = None
    if isinstance(candidate, Path):
        candidate_path = candidate
    elif isinstance(candidate, str):
        stripped = candidate.strip()
        if stripped:
            candidate_path = Path(stripped)
    if candidate_path is not None and not candidate_path.is_absolute():
        candidate_path = BASE_DIR / candidate_path
    if candidate_path == DEFAULT_REPORT and fallback != DEFAULT_REPORT:
        candidate_path = fallback
    chosen = candidate_path or fallback
    if not chosen.is_absolute():
        chosen = BASE_DIR / chosen
    return chosen


def load_results() -> tuple[list[str], list[int], list[str], StatusMap]:
    tests: list[str] = []
    durs: list[int] = []
    fails: list[str] = []
    statuses: StatusMap = {}
    if not LOG.exists():
        return tests, durs, fails, statuses
    with LOG.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            name = obj.get("name", "unknown")
            tests.append(name)
            value = obj.get("duration_ms")
            duration = int(value) if isinstance(value, (int, float)) else 0
            durs.append(duration)
            status = obj.get("status")
            entry_statuses = statuses.setdefault(name, set())
            if status is not None:
                entry_statuses.add(str(status))
                if status == "fail":
                    fails.append(name)
    return tests, durs, fails, statuses


def p95(values: list[int]) -> int:
    if not values:
        return 0
    try:
        # statistics.quantiles with n=20 approximates percentiles
        return int(statistics.quantiles(values, n=20)[18])
    except Exception:
        values_sorted = sorted(values)
        idx = math.ceil(0.95 * (len(values_sorted) - 1))
        capped_idx = min(idx, len(values_sorted) - 1)
        return int(values_sorted[capped_idx])


def main() -> None:
    manifest = load_reflection_manifest()
    tests, durs, fails, statuses = load_results()
    total = len(tests)
    if total == 0:
        pass_rate: float = 0.0
    else:
        pass_rate = (total - len(fails)) / total
    unique_tests = len(statuses)
    flaky_tests = sum(1 for vals in statuses.values() if {"pass", "fail"}.issubset(vals))
    if unique_tests == 0:
        flaky_rate = 0.0
    else:
        flaky_rate = flaky_tests / unique_tests
    dur_p95 = p95(durs)
    now = datetime.datetime.now(datetime.UTC).isoformat()
    report_path = load_report_output_path(manifest=manifest)
    include_why = load_report_include_why(manifest=manifest)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"# Reflection Report ({now} UTC)\n\n")
        f.write(f"- Total tests: {total}\n")
        f.write(f"- Pass rate: {pass_rate:.2%}\n")
        f.write(f"- Flaky rate: {flaky_rate:.2%}\n")
        f.write(f"- Duration p95: {dur_p95} ms\n")
        f.write(f"- Failures: {len(fails)}\n\n")
        if fails and include_why:
            f.write("## Why-Why (draft)\n")
            for name, cnt in Counter(fails).items():
                f.write(
                    f"- {name} (x{cnt}): 仮説=前処理の不安定/依存の競合/境界値不足\n"
                )

    # Issue候補のメモ（Actionsで拾ってIssue化）
    suggest_issues = load_actions_suggest_issues(manifest=manifest)
    issue_output_path = ISSUE_OUT
    if not issue_output_path.is_absolute():
        issue_output_path = BASE_DIR / issue_output_path
    if (
        issue_output_path.parent == DEFAULT_REPORT.parent
        and report_path.parent != DEFAULT_REPORT.parent
    ):
        issue_output_path = report_path.parent / issue_output_path.name
    if fails and suggest_issues:
        issue_output_path.parent.mkdir(parents=True, exist_ok=True)
        with issue_output_path.open("w", encoding="utf-8") as f:
            f.write("### 反省TODO\n")
            for name in sorted(set(fails)):
                f.write(f"- [ ] {name} の再現手順/前提/境界値を追加\n")
                f.write(f"- [ ] {name} の再現手順/前提/境界値の工程を増やす\n")
    elif issue_output_path.exists():
        issue_output_path.unlink()


if __name__ == "__main__":
    main()
