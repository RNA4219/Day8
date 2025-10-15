from __future__ import annotations

import datetime
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Final

from pathlib import Path

StatusMap = dict[str, set[str]]

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[2]
LOG: Final[Path] = BASE_DIR / "logs" / "test.jsonl"
REPORT: Final[Path] = BASE_DIR / "reports" / "today.md"
ISSUE_OUT: Final[Path] = BASE_DIR / "reports" / "issue_suggestions.md"


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
    now = datetime.datetime.utcnow().isoformat()

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
                    f"- {name}: 仮説=前処理の不安定/依存の競合/境界値不足\n"
                )

    # Issue候補のメモ（Actionsで拾ってIssue化）
    if fails:
        with ISSUE_OUT.open("w", encoding="utf-8") as f:
            f.write("### 反省TODO\n")
            for name in sorted(set(fails)):
                f.write(f"- [ ] {name} の再現手順/前提/境界値を追加\n")
                f.write(f"- [ ] {name} の再現手順/前提/境界値の工程を増やす\n")
    elif ISSUE_OUT.exists():
        ISSUE_OUT.unlink()


if __name__ == "__main__":
    main()
