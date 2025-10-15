from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence


BULLET_PATTERN = re.compile(r"^\s*[-*+]\s*(?:\[[xX ]\])?\s*")


def _normalize_pattern(pattern: str) -> str:
    normalized = pattern.lstrip("./")
    return normalized.replace("\\", "/")


def load_forbidden_patterns(policy_path: Path) -> List[str]:
    patterns: List[str] = []
    in_self_modification = False
    in_forbidden_paths = False
    forbidden_indent: int | None = None

    for raw_line in policy_path.read_text(encoding="utf-8").splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if stripped_line.endswith(":"):
            key = stripped_line[:-1].strip()
            if indent == 0:
                in_self_modification = key == "self_modification"
                in_forbidden_paths = False
                forbidden_indent = None
            elif in_self_modification and key == "forbidden_paths":
                in_forbidden_paths = True
                forbidden_indent = indent
            elif indent <= (forbidden_indent or indent):
                in_forbidden_paths = False
            continue

        if in_forbidden_paths and stripped_line.startswith("- "):
            value = stripped_line[2:].strip()
            if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
                value = value[1:-1]
            if value:
                patterns.append(value.lstrip("/"))
            continue

        if in_forbidden_paths and indent <= (forbidden_indent or indent):
            in_forbidden_paths = False

    return patterns


def get_changed_paths(refspec: str) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", refspec],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_forbidden_matches(paths: Iterable[str], patterns: Sequence[str]) -> List[str]:
    normalized_patterns = [_normalize_pattern(pattern) for pattern in patterns]
    matches: List[str] = []
    for path in paths:
        normalized_path = path.lstrip("./")
        normalized_path = normalized_path.replace("\\", "/")
        posix_path = PurePosixPath(normalized_path)
        for normalized_pattern in normalized_patterns:
            if normalized_pattern.endswith("/**"):
                base_pattern = normalized_pattern[:-3].rstrip("/")
                if not base_pattern:
                    matches.append(normalized_path)
                    break
                base_path = PurePosixPath(base_pattern)
                if posix_path == base_path or posix_path.is_relative_to(base_path):
                    matches.append(normalized_path)
                    break
            elif posix_path.match(normalized_pattern):
                matches.append(normalized_path)
                break
    return matches


def read_event_body(event_path: Path) -> str | None:
    if not event_path.exists():
        return None
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    body = pull_request.get("body")
    if body is None:
        return None
    if not isinstance(body, str):
        return None
    return body


def validate_priority_score(body: str | None) -> tuple[bool, str | None]:
    if not body:
        return False, "Priority Score セクションが見つかりません"

    normalized_body = "\n".join(
        BULLET_PATTERN.sub("", line) for line in body.splitlines()
    )
    pattern = re.compile(r"^Priority Score:\s*(?P<content>.+)$", re.MULTILINE)
    match = pattern.search(normalized_body)
    if not match:
        return False, "Priority Score の記載が見つかりません"

    content: str = match.group("content")
    if "/" not in content:
        return False, "Priority Score の根拠が不足しています"

    score_raw, reason_raw = [segment.strip() for segment in content.split("/", 1)]

    if not score_raw:
        return False, "Priority Score の数値が不足しています"
    if not reason_raw:
        return False, "Priority Score の根拠が不足しています"

    try:
        score_value = float(score_raw)
    except ValueError:
        return False, "Priority Score の数値が不正です"

    if not math.isfinite(score_value):
        return False, "Priority Score の数値が有限ではありません"

    return True, None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    policy_path = repo_root / "governance" / "policy.yaml"
    forbidden_patterns = load_forbidden_patterns(policy_path)

    try:
        changed_paths = get_changed_paths("origin/main...")
    except subprocess.CalledProcessError as error:
        print(f"Failed to collect changed paths: {error}", file=sys.stderr)
        return 1
    violations = find_forbidden_matches(changed_paths, forbidden_patterns)
    if violations:
        print(
            "Forbidden path modifications detected:\n" + "\n".join(f" - {path}" for path in violations),
            file=sys.stderr,
        )
        return 1

    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path_value:
        print("GITHUB_EVENT_PATH is not set", file=sys.stderr)
        return 1
    body = read_event_body(Path(event_path_value))
    is_valid, error = validate_priority_score(body)
    if not is_valid:
        print(error or "Priority Score が無効です", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
