from __future__ import annotations

import ast
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence


MARKDOWN_EMPHASIS_PATTERN = re.compile(r"(?<!\\)(\*\*|__|\*|_)(?P<content>.*?)(?<!\\)\1")

BULLET_PATTERN = re.compile(r"^\s*(?:[-*+]\s*(?:\[[xX ]\])?\s*|\d+[.)]\s*)")

PRIORITY_LABEL_PATTERN = re.compile(r"^(Priority\s*Score)\s*[:：]\s*")

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_NAME = REPO_ROOT.name


def _normalize_pattern(pattern: str) -> str:
    normalized = pattern.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("/"):
        normalized = normalized[1:]
    prefix = f"{REPO_ROOT_NAME}/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix) :]
    return normalized


def _strip_inline_comment(value: str) -> str:
    in_single_quote = False
    in_double_quote = False
    escaped = False

    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double_quote:
            escaped = True
            continue
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            continue
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            continue
        if char == "#" and not in_single_quote and not in_double_quote:
            if index == 0 or value[index - 1].isspace():
                return value[:index]
    return value


def _parse_inline_array(value: str) -> List[str]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    normalized_values: List[str] = []
    for item in parsed:
        if isinstance(item, str):
            stripped_item = item.strip()
            if stripped_item:
                normalized_values.append(_normalize_pattern(stripped_item))
    return normalized_values


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
        line_without_comments = _strip_inline_comment(stripped_line).rstrip()
        if not line_without_comments:
            continue

        if in_self_modification and line_without_comments.startswith("forbidden_paths:"):
            remainder = line_without_comments[len("forbidden_paths:") :].strip()
            if remainder:
                inline_patterns = _parse_inline_array(remainder)
                if inline_patterns:
                    patterns.extend(inline_patterns)
                in_forbidden_paths = False
                forbidden_indent = None
                continue

        if line_without_comments.endswith(":"):
            key = line_without_comments[:-1].strip()
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
            raw_value = stripped_line[2:]
            without_comments = _strip_inline_comment(raw_value).strip()
            unquoted_value = without_comments
            if (
                len(unquoted_value) >= 2
                and unquoted_value[0] in {'"', "'"}
                and unquoted_value[-1] == unquoted_value[0]
            ):
                unquoted_value = unquoted_value[1:-1].strip()
            if unquoted_value:
                patterns.append(_normalize_pattern(unquoted_value))
            continue

        if in_forbidden_paths and indent <= (forbidden_indent or indent):
            in_forbidden_paths = False

    return patterns


def get_changed_paths(refspec: str, repo_root: Path | None = None) -> List[str]:
    root = repo_root or REPO_ROOT
    result = subprocess.run(
        ["git", "diff", "--name-only", refspec],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=root,
    )
    normalized_paths: List[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized_paths.append(_normalize_path(stripped))
    return normalized_paths
def find_forbidden_matches(paths: Iterable[str], patterns: Sequence[str]) -> List[str]:
    normalized_patterns = [_normalize_pattern(pattern) for pattern in patterns]
    matches: List[str] = []
    for path in paths:
        normalized_path = _normalize_path(path)
        posix_path = PurePosixPath(normalized_path)
        for normalized_pattern in normalized_patterns:
            if normalized_pattern.endswith("/**"):
                base_pattern = normalized_pattern[:-3].rstrip("/")
                if not base_pattern:
                    matches.append(normalized_path)
                    break
                contains_glob = any(char in base_pattern for char in "*?[]")
                if contains_glob:
                    matched = False
                    for candidate in (posix_path,) + tuple(posix_path.parents):
                        if candidate == PurePosixPath("."):
                            continue
                        if candidate.match(base_pattern):
                            matches.append(normalized_path)
                            matched = True
                            break
                    if matched:
                        break
                    if posix_path.match(normalized_pattern):
                        matches.append(normalized_path)
                        break
                else:
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


def _strip_markdown_emphasis(text: str) -> str:
    previous = None
    result = text
    while previous != result:
        previous = result
        result = MARKDOWN_EMPHASIS_PATTERN.sub(lambda match: match.group("content"), result)
    return result


def _normalize_priority_line(line: str) -> str:
    without_emphasis = _strip_markdown_emphasis(line)
    without_bullet = BULLET_PATTERN.sub("", without_emphasis).lstrip()
    if not without_bullet:
        return without_bullet
    normalized = PRIORITY_LABEL_PATTERN.sub("Priority Score: ", without_bullet, count=1)
    return normalized


def validate_priority_score(body: str | None) -> tuple[bool, str | None]:
    if not body:
        return False, "Priority Score セクションが見つかりません"

    normalized_body = "\n".join(_normalize_priority_line(line) for line in body.splitlines())
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
        changed_paths = get_changed_paths("origin/main...", repo_root=repo_root)
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
