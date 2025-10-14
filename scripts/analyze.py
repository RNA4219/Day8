import datetime
import json
import math
import pathlib
import statistics
from collections import Counter

LOG = pathlib.Path("logs/test.jsonl")
REPORT = pathlib.Path("reports/today.md")
ISSUE_OUT = pathlib.Path("reports/issue_suggestions.md")


def load_results():
    tests, durs, fails = [], [], []
    if not LOG.exists():
        return tests, durs, fails
    with LOG.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tests.append(obj.get("name", "unknown"))
            raw_duration = obj.get("duration_ms", 0)
            try:
                if raw_duration is None:
                    raise TypeError
                duration = int(raw_duration)
            except (TypeError, ValueError):
                duration = 0
            durs.append(duration)
            if obj.get("status") == "fail":
                fails.append(obj.get("name", "unknown"))
    return tests, durs, fails


def p95(values):
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


def main():
    tests, durs, fails = load_results()
    total = len(tests) or 1
    pass_rate = (total - len(fails)) / total
    dur_p95 = p95(durs)
    now = datetime.datetime.utcnow().isoformat()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8") as f:
        f.write(f"# Reflection Report ({now} UTC)\n\n")
        f.write(f"- Total tests: {total}\n")
        f.write(f"- Pass rate: {pass_rate:.2%}\n")
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


if __name__ == "__main__":
    main()
