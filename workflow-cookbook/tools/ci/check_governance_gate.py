from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence


REPO_ROOT_NAME = Path(__file__).resolve().parents[2].name


@dataclass(frozen=True)
class MessageLocation:
    source: str
    line: int | None = None


def _print_warning(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _format_message(prefix: str, message: str, location: MessageLocation | None) -> str:
    if location is None:
        return f"{prefix}: {message}"
    if location.line is not None:
        return f"{prefix}: {location.source}:{location.line}: {message}"
    return f"{prefix}: {location.source}: {message}"


def _normalize_markdown_emphasis(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "").replace("~~", "").replace("`", "")
    cleaned = re.sub(r"(?m)^(\s*[-*+]\s*)\[[xX ]\]\s*", r"\1", cleaned)
    cleaned = re.sub(r"(^|\s)\*+([^\s])", r"\1\2", cleaned)
    cleaned = re.sub(r"([^\s])\*+(\s|$)", r"\1\2", cleaned)
    cleaned = re.sub(r"(^|\s)_+([^\s])", r"\1\2", cleaned)
    cleaned = re.sub(r"([^\s])_+(\s|$)", r"\1\2", cleaned)
    return unicodedata.normalize("NFKC", cleaned)


def _strip_markup_links(text: str) -> str:
    without_inline = _INLINE_LINK_PATTERN.sub(r"\1", text)
    without_reference = _REFERENCE_LINK_PATTERN.sub(r"\1", without_inline)
    return _HTML_TAG_PATTERN.sub("", without_reference)


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
PR_BODY_SOURCE_NAME = "PR_BODY"
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


def load_event_payload(event_path: Path) -> dict[str, object] | None:
    if not event_path.exists():
        _print_warning(f"{event_path}: Event payload not found")
        return None
    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _print_warning(f"{event_path}: Cannot read event payload: {error}")
        return None
    if not isinstance(payload, dict):
        _print_warning(f"{event_path}: Event payload must be a JSON object")
        return None
    return payload


def read_event_body(event_path: Path) -> str | None:
    payload = load_event_payload(event_path)
    if payload is None:
        return None
    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    body = pull_request.get("body")
    if body is None:
        return None
    if not isinstance(body, str):
        return None
    return body


def resolve_pr_body_with_source() -> tuple[str | None, str | Path | None]:
    direct_body = os.environ.get("PR_BODY")
    if direct_body is not None:
        return direct_body, PR_BODY_SOURCE_NAME

    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path_value:
        print(
            "PR body data is unavailable. Set PR_BODY or GITHUB_EVENT_PATH.",
            file=sys.stderr,
        )
        return None, None

    event_path = Path(event_path_value)
    return read_event_body(event_path), event_path if event_path.exists() else None


def resolve_pr_body() -> str | None:
    body, _ = resolve_pr_body_with_source()
    return body


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Governance gate validator")
    parser.add_argument(
        "--pr-body",
        dest="pr_body",
        type=str,
        help="Pull request body content",
    )
    parser.add_argument(
        "--pr-body-file",
        dest="pr_body_file",
        type=Path,
        help="Path to file containing pull request body",
    )
    return parser.parse_args(list(argv))


_OPTIONAL_PARENTHETICAL = r"(?:\s*[\(（][^\n\r\)）]*[\)）])?"
_LABEL_SEPARATOR_TOKENS: tuple[str, ...] = (":", "：", "-", "－", "–", "—")
_LABEL_SEPARATOR_PATTERN = "|".join(re.escape(token) for token in _LABEL_SEPARATOR_TOKENS)
_LABEL_SEPARATOR_REGEX = rf"\s*(?:{_LABEL_SEPARATOR_PATTERN})\s*"
_INLINE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_REFERENCE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\s*\[[^\]]+\]")
_HTML_TAG_PATTERN = re.compile(r"</?[^>]+>")


INTENT_PATTERN = re.compile(
    rf"Intent{_OPTIONAL_PARENTHETICAL}{_LABEL_SEPARATOR_REGEX}INT-[0-9A-Z]+(?:-[0-9A-Z]+)*",
    re.IGNORECASE,
)
EVALUATION_HEADING_PATTERN = re.compile(
    r"^#{2,6}\s*EVALUATION\b",
    re.IGNORECASE | re.MULTILINE,
)
EVALUATION_HTML_HEADING_PATTERN = re.compile(
    r"<h[2-6][^>]*>\s*EVALUATION\b",
    re.IGNORECASE,
)
EVALUATION_ANCHOR_PATTERN = re.compile(
    r"(?:EVALUATION\.md)?#acceptance-criteria",
    re.IGNORECASE,
)
PRIORITY_LABEL_PATTERN = re.compile(
    rf"Priority\s*Score{_OPTIONAL_PARENTHETICAL}{_LABEL_SEPARATOR_REGEX}",
    re.IGNORECASE,
)
PRIORITY_ENTRY_PATTERN = re.compile(
    rf"Priority\s*Score{_OPTIONAL_PARENTHETICAL}{_LABEL_SEPARATOR_REGEX}\d+(?:\.\d+)?\s*/",
    re.IGNORECASE,
)
_PRIORITY_STRIP_CHARS = " \t\r\n\u3000"
_PRIORITY_PREFIX_CHARS = "-*+>•\u2022"

PRIORITY_SCORE_ERROR_MESSAGE = (
    "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
)


def _find_priority_label_line(body: str) -> int | None:
    for index, line in enumerate(body.splitlines(), 1):
        normalized_line = _strip_markup_links(_normalize_markdown_emphasis(line))
        if PRIORITY_LABEL_PATTERN.search(line) or PRIORITY_LABEL_PATTERN.search(normalized_line):
            return index
    return None


def _clean_priority_justification_line(line: str) -> str:
    stripped = line.strip(_PRIORITY_STRIP_CHARS)
    stripped = stripped.lstrip(_PRIORITY_PREFIX_CHARS)
    stripped = stripped.lstrip(_PRIORITY_STRIP_CHARS)
    return stripped


def _has_priority_with_justification(body: str, has_priority_label: bool) -> bool:
    if not has_priority_label:
        return False

    for match in PRIORITY_ENTRY_PATTERN.finditer(body):
        remainder = body[match.end() :]
        lines = remainder.splitlines()
        if not lines:
            continue

        first_line = _clean_priority_justification_line(lines[0])
        if first_line:
            return True

        for line in lines[1:]:
            raw = line.strip(_PRIORITY_STRIP_CHARS)
            if not raw:
                continue
            if raw.startswith("```"):
                break
            if raw.startswith("#"):
                heading_level = len(raw) - len(raw.lstrip("#"))
                if heading_level <= 2:
                    break
                continue

            cleaned = _clean_priority_justification_line(line)
            if cleaned:
                return True

    return False


def validate_pr_body(body: str | None, *, source: str | Path | None = None) -> bool:
    raw_body = body or ""
    normalized_body = _normalize_markdown_emphasis(raw_body)
    search_body = _strip_markup_links(normalized_body)
    has_priority_label = bool(PRIORITY_LABEL_PATTERN.search(search_body))
    normalized_priority_body = PRIORITY_LABEL_PATTERN.sub("Priority Score: ", search_body)
    has_priority_with_justification = _has_priority_with_justification(
        normalized_priority_body, has_priority_label
    )
    source_text = str(source) if source is not None else None
    warnings: list[tuple[str, MessageLocation | None]] = []
    errors: list[tuple[str, MessageLocation | None]] = []

    if not INTENT_PATTERN.search(search_body):
        intent_location = MessageLocation(source_text, 1) if source_text else None
        warnings.append(("PR body should include 'Intent: INT-xxx'", intent_location))
        errors.append(("PR body should include 'Intent: INT-xxx'", intent_location))
    has_evaluation_heading = bool(
        EVALUATION_HEADING_PATTERN.search(normalized_body)
        or EVALUATION_HTML_HEADING_PATTERN.search(raw_body)
    )
    has_evaluation_anchor = bool(
        EVALUATION_ANCHOR_PATTERN.search(raw_body)
        or EVALUATION_ANCHOR_PATTERN.search(normalized_body)
    )
    evaluation_warning_needed = not (has_evaluation_heading and has_evaluation_anchor)
    if evaluation_warning_needed:
        evaluation_location = MessageLocation(source_text, None) if source_text else None
        warnings.append(("PR must reference EVALUATION (acceptance) anchor", evaluation_location))
    priority_location: MessageLocation | None = None
    if source_text:
        priority_line = _find_priority_label_line(raw_body) if has_priority_label else None
        priority_location = MessageLocation(source_text, priority_line)
    if not has_priority_label or not has_priority_with_justification:
        warnings.append((PRIORITY_SCORE_ERROR_MESSAGE, priority_location))
        errors.append((PRIORITY_SCORE_ERROR_MESSAGE, priority_location))

    for warning, location in warnings:
        print(_format_message("Warning", warning, location), file=sys.stderr)
    for error, location in errors:
        print(_format_message("Error", error, location), file=sys.stderr)

    return not errors


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = ()
    args = parse_args(argv)

    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name and event_name != "pull_request":
        _print_warning(f"Skipping governance gate (event={event_name})")
        return 0

    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    if event_name == "pull_request":
        if not event_path_value:
            _print_warning("Skipping governance gate (event payload unavailable)")
            return 0
        event_payload = load_event_payload(Path(event_path_value))
        if event_payload is None:
            _print_warning("Skipping governance gate (event payload unreadable)")
            return 0
        pull_request_data = event_payload.get("pull_request")
        if not isinstance(pull_request_data, dict):
            _print_warning("Skipping governance gate (pull request payload missing)")
            return 0
        if pull_request_data.get("draft"):
            _print_warning("Skipping governance gate (draft pull request)")
            return 0
        repository_data = event_payload.get("repository")
        default_branch: str | None = None
        if isinstance(repository_data, dict):
            default_branch_value = repository_data.get("default_branch")
            if isinstance(default_branch_value, str):
                default_branch = default_branch_value
        base_data = pull_request_data.get("base")
        base_ref: str | None = None
        if isinstance(base_data, dict):
            base_ref_value = base_data.get("ref")
            if isinstance(base_ref_value, str):
                base_ref = base_ref_value
        if default_branch and base_ref and base_ref != default_branch:
            _print_warning(
                f"Skipping governance gate (base={base_ref}, default_branch={default_branch})"
            )
            return 0

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

    body: str | None = None
    body_source: str | Path | None = None
    if args.pr_body is not None:
        body = args.pr_body
        body_source = PR_BODY_SOURCE_NAME
    elif args.pr_body_file is not None:
        try:
            body = args.pr_body_file.read_text(encoding="utf-8")
            body_source = args.pr_body_file
        except OSError as error:
            print(f"Failed to read PR body file: {error}", file=sys.stderr)
            return 1
    else:
        body, inferred_source = resolve_pr_body_with_source()
        if inferred_source is not None:
            body_source = inferred_source
    if body is None:
        return 0
    if not validate_pr_body(body, source=body_source):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
