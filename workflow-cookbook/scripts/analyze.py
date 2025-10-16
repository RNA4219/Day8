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
REPORT: Final[Path] = WORKFLOW_ROOT / "reports" / "today.md"
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


def _fallback_read_suggest_issues(text: str, default: bool) -> bool:
    in_actions = False
    actions_indent = 0
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if stripped.startswith("actions:") and indent == 0:
            in_actions = True
            actions_indent = indent
            continue
        if indent <= actions_indent:
            in_actions = False
        if in_actions and stripped.startswith("suggest_issues:"):
            value = stripped.split(":", 1)[1].split("#", 1)[0]
            coerced = _coerce_bool(value)
            return coerced if coerced is not None else default
    return default


def _fallback_manifest_from_text(text: str, default_suggest_issues: bool) -> dict[str, Any]:
    return {
        "actions": {
            "suggest_issues": _fallback_read_suggest_issues(text, default_suggest_issues)
        }
    }


def load_reflection_manifest(
    path: Path | None = None, default_suggest_issues: bool = True
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
        return _fallback_manifest_from_text(text, default_suggest_issues)
    try:
        loaded = yaml.safe_load(text)
    except Exception:
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def load_actions_suggest_issues(
    path: Path | None = None, default: bool = True
) -> bool:
    manifest = load_reflection_manifest(path, default_suggest_issues=default)
    if not manifest:
        return default
    actions: Any = manifest.get("actions")
    if isinstance(actions, dict):
        suggest = actions.get("suggest_issues")
        coerced = _coerce_bool(suggest)
        if coerced is not None:
            return coerced
    return default


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

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8") as f:
        f.write(f"# Reflection Report ({now} UTC)\n\n")
        f.write(f"- Total tests: {total}\n")
        f.write(f"- Pass rate: {pass_rate:.2%}\n")
        f.write(f"- Flaky rate: {flaky_rate:.2%}\n")
        f.write(f"- Duration p95: {dur_p95} ms\n")
        f.write(f"- Failures: {len(fails)}\n\n")
        if fails:
            f.write("## Why-Why (draft)\n")
            for name, cnt in Counter(fails).items():
                f.write(
                    f"- {name} (x{cnt}): 仮説=前処理の不安定/依存の競合/境界値不足\n"
                )

    # Issue候補のメモ（Actionsで拾ってIssue化）
    suggest_issues = load_actions_suggest_issues()
    if fails and suggest_issues:
        with ISSUE_OUT.open("w", encoding="utf-8") as f:
            f.write("### 反省TODO\n")
            for name in sorted(set(fails)):
                f.write(f"- [ ] {name} の再現手順/前提/境界値を追加\n")
                f.write(f"- [ ] {name} の再現手順/前提/境界値の工程を増やす\n")
    elif ISSUE_OUT.exists():
        ISSUE_OUT.unlink()


if __name__ == "__main__":
    main()
