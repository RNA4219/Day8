from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, List, Sequence


def _normalize_markdown_emphasis(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "").replace("~~", "").replace("`", "")
    cleaned = re.sub(r"(?m)^(\s*[-*+]\s*)\[[xX ]\]\s*", r"\1", cleaned)
    cleaned = re.sub(r"(^|\s)\*+([^\s])", r"\1\2", cleaned)
    cleaned = re.sub(r"([^\s])\*+(\s|$)", r"\1\2", cleaned)
    cleaned = re.sub(r"(^|\s)_+([^\s])", r"\1\2", cleaned)
    cleaned = re.sub(r"([^\s])_+(\s|$)", r"\1\2", cleaned)
    return cleaned


def _strip_inline_comment(text: str) -> str:
    in_single = False
    in_double = False
    result: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "#" and not in_single and not in_double:
            break
        result.append(char)
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "\\" and in_double:
            index += 1
            if index < length:
                result.append(text[index])
        index += 1
    return "".join(result).rstrip()


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
        content = _strip_inline_comment(stripped_line)
        if not content:
            continue

        if content.endswith(":"):
            key = content[:-1].strip()
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

        if in_forbidden_paths and content.startswith("- "):
            value = content[2:].strip()
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


DEFAULT_DIFF_REFSPECS: Sequence[str] = ("origin/main...", "main...", "HEAD")


def collect_changed_paths(refspecs: Sequence[str] = DEFAULT_DIFF_REFSPECS) -> List[str]:
    last_error: subprocess.CalledProcessError | None = None
    for refspec in refspecs:
        try:
            return get_changed_paths(refspec)
        except subprocess.CalledProcessError as error:
            last_error = error
    if last_error is not None:
        raise last_error
    return []


def find_forbidden_matches(paths: Iterable[str], patterns: Sequence[str]) -> List[str]:
    matches: List[str] = []
    for path in paths:
        normalized_path = path.lstrip("./")
        for pattern in patterns:
            if fnmatch(normalized_path, pattern):
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


def resolve_pr_body() -> str | None:
    direct_body = os.environ.get("PR_BODY")
    if direct_body is not None:
        return direct_body

    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path_value:
        print(
            "PR body data is unavailable. Set PR_BODY or GITHUB_EVENT_PATH.",
            file=sys.stderr,
        )
        return None

    return read_event_body(Path(event_path_value))


INTENT_PATTERN = re.compile(
    r"Intent\s*[：:]\s*INT-[0-9A-Z]+(?:-[0-9A-Z]+)*",
    re.IGNORECASE,
)
EVALUATION_HEADING_PATTERN = re.compile(
    r"^#{2,6}\s*EVALUATION\b",
    re.IGNORECASE | re.MULTILINE,
)
EVALUATION_ANCHOR_PATTERN = re.compile(
    r"EVALUATION\.md#acceptance-criteria",
    re.IGNORECASE,
)
PRIORITY_LABEL_PATTERN = re.compile(
    r"Priority\s*Score\s*[：:]\s*",
    re.IGNORECASE,
)
PRIORITY_PATTERN = re.compile(
    r"Priority\s*Score\s*:\s*\d+(?:\.\d+)?\s*/\s*\S.*",
    re.IGNORECASE,
)


def validate_pr_body(body: str | None) -> bool:
    normalized_body = _normalize_markdown_emphasis(body or "")
    has_priority_label = bool(PRIORITY_LABEL_PATTERN.search(normalized_body))
    normalized_body = PRIORITY_LABEL_PATTERN.sub("Priority Score: ", normalized_body)
    success = True

    if not INTENT_PATTERN.search(normalized_body):
        print("PR body must include 'Intent: INT-xxx'", file=sys.stderr)
        success = False
    has_evaluation_heading = bool(EVALUATION_HEADING_PATTERN.search(normalized_body))
    has_evaluation_anchor = bool(EVALUATION_ANCHOR_PATTERN.search(normalized_body))
    if not has_evaluation_heading or not has_evaluation_anchor:
        print("PR must reference EVALUATION (acceptance) anchor", file=sys.stderr)
        success = False
    if not PRIORITY_PATTERN.search(normalized_body):
        print(
            "PR must include 'Priority Score: <number>' to reflect Acceptance Criteria prioritization",
            file=sys.stderr,
        )
        success = False

    return success


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    policy_path = repo_root / "governance" / "policy.yaml"
    forbidden_patterns = load_forbidden_patterns(policy_path)

    try:
        changed_paths = collect_changed_paths()
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

    body = resolve_pr_body()
    if body is None:
        return 1
    if not validate_pr_body(body):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
