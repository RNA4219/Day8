from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import ast
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence


REPO_ROOT_NAME = Path(__file__).resolve().parents[2].name


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


def _extend_inline_sequence(sequence_text: str, patterns: list[str]) -> bool:
    try:
        parsed = ast.literal_eval(sequence_text)
    except (SyntaxError, ValueError):
        return False
    if isinstance(parsed, (list, tuple)):
        appended = False
        for item in parsed:
            if isinstance(item, str) and item:
                patterns.append(item.lstrip("/"))
                appended = True
        return appended
    return False


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

        if ":" in content:
            key_part, value_part = content.split(":", 1)
            key = key_part.strip()
            value = value_part.strip()
            if indent == 0:
                in_self_modification = key == "self_modification"
                in_forbidden_paths = False
                forbidden_indent = None
            elif in_self_modification and key == "forbidden_paths":
                if value.startswith("[") and value.endswith("]"):
                    _extend_inline_sequence(value, patterns)
                in_forbidden_paths = False
                forbidden_indent = None
            elif indent <= (forbidden_indent or indent):
                in_forbidden_paths = False
            continue

        if in_forbidden_paths and content.startswith("- "):
            value = content[2:].strip()
            if value.startswith("[") and value.endswith("]"):
                if _extend_inline_sequence(value, patterns):
                    continue
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


def _detect_repo_name() -> str:
    resolved = Path(__file__).resolve()
    parents = list(resolved.parents)
    for parent in parents:
        if (parent / ".git").exists():
            return parent.name
    return parents[-1].name if parents else resolved.name


_REPO_NAME = _detect_repo_name()
_PREFIXES_TO_REMOVE: tuple[str, ...] = tuple(
    prefix for prefix in {"workflow-cookbook", _REPO_NAME} if prefix
)


def _normalize_changed_path(path: str) -> str:
    stripped = path.strip()
    if not stripped:
        return stripped
    cleaned = stripped.replace("\\", "/").lstrip("./")
    posix_path = PurePosixPath(cleaned)
    parts = list(posix_path.parts)
    while parts and parts[0] in _PREFIXES_TO_REMOVE:
        parts.pop(0)
    if not parts:
        return str(posix_path)
    return "/".join(parts)


def _generate_pattern_variants(pattern: str) -> tuple[str, ...]:
    variants: list[str] = [pattern]
    stripped = pattern
    while stripped.startswith("**/"):
        stripped = stripped[3:]
        if not stripped:
            break
        if stripped not in variants:
            variants.append(stripped)
        else:
            break
    return tuple(variants)


def find_forbidden_matches(paths: Iterable[str], patterns: Sequence[str]) -> List[str]:
    matches: List[str] = []
    normalized_patterns: list[tuple[str, ...]] = []
    for pattern in patterns:
        normalized_pattern = _normalize_changed_path(pattern)
        if not normalized_pattern:
            continue
        normalized_patterns.append(_generate_pattern_variants(normalized_pattern))
    for path in paths:
        normalized_path = _normalize_changed_path(path)
        if not normalized_path:
            continue
        posix_path = PurePosixPath(normalized_path)
        for variants in normalized_patterns:
            matched = False
            for candidate in variants:
                if posix_path.match(candidate):
                    matches.append(normalized_path)
                    matched = True
                    break
                if candidate.endswith("/**") and "**" in candidate:
                    base = candidate[:-3].rstrip("/")
                    if not base or posix_path.is_relative_to(base):
                        matches.append(normalized_path)
                        matched = True
                        break
            if matched:
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

PRIORITY_SCORE_ERROR_MESSAGE = (
    "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
)


def validate_pr_body(body: str | None) -> bool:
    normalized_body = _normalize_markdown_emphasis(body or "")
    has_priority_label = bool(PRIORITY_LABEL_PATTERN.search(normalized_body))
    normalized_body = PRIORITY_LABEL_PATTERN.sub("Priority Score: ", normalized_body)
    priority_match = PRIORITY_PATTERN.search(normalized_body) if has_priority_label else None
    has_priority_with_justification = priority_match is not None
    success = True

    if not INTENT_PATTERN.search(normalized_body):
        print("PR body must include 'Intent: INT-xxx'", file=sys.stderr)
        success = False
    has_evaluation_heading = bool(EVALUATION_HEADING_PATTERN.search(normalized_body))
    has_evaluation_anchor = bool(EVALUATION_ANCHOR_PATTERN.search(normalized_body))
    if not has_evaluation_heading or not has_evaluation_anchor:
        print("PR must reference EVALUATION (acceptance) anchor", file=sys.stderr)
        success = False
    if not has_priority_label or not has_priority_with_justification:
        print(PRIORITY_SCORE_ERROR_MESSAGE, file=sys.stderr)
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
