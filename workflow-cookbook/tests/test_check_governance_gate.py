import json
import re
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ci import check_governance_gate
from tools.ci.check_governance_gate import (
    EVALUATION_SECTION_ERROR_MESSAGE,
    PRIORITY_SCORE_ERROR_MESSAGE,
    find_forbidden_matches,
    load_forbidden_patterns,
    validate_pr_body,
)


@pytest.mark.parametrize(
    "changed_paths, patterns, expected",
    [
        (
            """workflow-cookbook/core/schema/model.yaml\ndocs/guide.md""".splitlines(),
            ["/core/schema/**"],
            ["core/schema/model.yaml"],
        ),
        ("""core/schema/model.yaml\ndocs/guide.md""".splitlines(), ["/core/schema/**"], ["core/schema/model.yaml"]),
        (
            ["workflow-cookbook/core/schema/model.yaml"],
            ["/core/schema/**"],
            ["core/schema/model.yaml"],
        ),
        (
            ["workflow-cookbook/core/schema/model.yaml"],
            ["workflow-cookbook/core/schema/**"],
            ["core/schema/model.yaml"],
        ),
        (
            ["schema/model.yaml"],
            ["**/schema/**"],
            ["schema/model.yaml"],
        ),
        (
            ["workflow-cookbook/governance/policy.yaml"],
            ["/governance/**"],
            ["governance/policy.yaml"],
        ),
        ("""docs/readme.md\nops/runbook.md""".splitlines(), ["/core/schema/**"], []),
        (
            """auth/service.py\ncore/schema/definitions.yml""".splitlines(),
            ["/auth/**", "/core/schema/**"],
            ["auth/service.py", "core/schema/definitions.yml"],
        ),
        (
            """core/schema/v1/model.yaml\nauth/service/internal/api.py""".splitlines(),
            ["/core/schema/**", "/auth/**"],
            ["core/schema/v1/model.yaml", "auth/service/internal/api.py"],
        ),
    ],
)
def test_find_forbidden_matches(changed_paths, patterns, expected):
    normalized = [pattern.lstrip("/") for pattern in patterns]
    assert find_forbidden_matches(changed_paths, normalized) == expected


def test_find_forbidden_matches_with_repo_subdir_prefix(monkeypatch):
    monkeypatch.setattr(check_governance_gate, "REPO_ROOT_NAME", "Day8")

    matches = find_forbidden_matches(
        ["workflow-cookbook/core/schema/model.yaml"],
        ["core/schema/**"],
    )

    assert matches == ["core/schema/model.yaml"]


def test_validate_pr_body_success(capsys):
    body = """
Intent: INT-123
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 4.5 / 安全性強化
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_segmented_intent(capsys):
    body = """
Intent: INT-2024-001
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 3 / レイテンシ改善
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_alphanumeric_segments(capsys):
    body = """
Intent: INT-OPS-7A
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 2 / セキュリティ強化
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_fullwidth_colon(capsys):
    body = """
Intent：INT-456
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score：1 / 重要顧客要望
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_parenthetical_labels(capsys):
    body = """
Intent（必須）: INT-5150
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score（必須）: 5 / 緊急度が高い
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_fullwidth_forms(capsys):
    body = """\
Ｉｎｔｅｎｔ：ＩＮＴ－１２３
＃＃ ＥＶＡＬＵＡＴＩＯＮ
- [Acceptance Criteria](../ＥＶＡＬＵＡＴＩＯＮ．ｍｄ＃ａｃｃｅｐｔａｎｃｅ－ｃｒｉｔｅｒｉａ)
Ｐｒｉｏｒｉｔｙ Ｓｃｏｒｅ：５ ／ フルワイド記法対応
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


@pytest.mark.parametrize(
    "priority_line",
    [
        "Priority Score：4 / 規制対応",  # 全角コロン
        "Priority Score ： 4 / 技術的負債削減",  # コロン前後に全角空白
        "Priority Score :4 / 顧客影響",  # コロン後に空白なし
        "Priority Score: 4 / 品質改善",  # 標準ケース
    ],
)
def test_validate_priority_score_accepts_colon_variants(priority_line, capsys):
    body = f"""
Intent: INT-001
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
{priority_line}
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


@pytest.mark.parametrize(
    "priority_line",
    [
        "**Priority Score:** 5 / 理由",
        "_Priority Score:_ 4 / 根拠",
        "- [x] **Priority Score:** 3 / 完了済み対策",
    ],
)
def test_validate_priority_score_accepts_emphasis(priority_line, capsys):
    body = f"""
Intent: INT-314
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
{priority_line}
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_priority_score_accepts_multiline_justification(capsys):
    body = """
Intent: INT-515
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 6 /
  - impact_scope=0.4
    - mitigates risk of regression
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_dash_separators(capsys):
    body = """
Intent - INT-880
## EVALUATION
- [Acceptance Criteria](#acceptance-criteria)
Priority Score - 5 / レビュー指摘対応
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_link_wrapped_identifiers(capsys):
    body = """
Intent: [INT-4242](https://tracker.example/INT-4242)
<h2>EVALUATION</h2>
- <a href="../EVALUATION.md#acceptance-criteria">Acceptance Criteria</a>
Priority Score: [5](https://tracker.example/priorities/5) / リンク付き根拠
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_rejects_priority_without_justification(capsys):
    body = """
Intent: INT-777
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 3
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert (
        "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
        in captured.err
    )
    assert "Error:" not in captured.err


INVALID_PRIORITY_LINES = [
    "",
    "Priority Score:",
    "Priority Score: 4",
    "Priority Score: 4 /",
    "Priority Score: 4 /   ",
    "Priority Score: high / 顧客要望",
    "Priority Score 4 / 品質改善",
]


def _build_priority_body(priority_line: str) -> str:
    lines = [
        "Intent: INT-4242",
        "## EVALUATION",
        "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
    ]
    if priority_line:
        lines.append(priority_line)
    return "\n".join(lines)


@pytest.mark.parametrize("priority_line", INVALID_PRIORITY_LINES)
def test_validate_pr_body_rejects_missing_priority_details(priority_line, capsys):
    body = _build_priority_body(priority_line)

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert (
        "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
        in captured.err
    )
    assert "Error:" not in captured.err


@pytest.mark.parametrize(
    "body",
    [
        "\n".join(
            [
                "Intent: INT-5150",
                "## EVALUATION",
                "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
            ]
        ),
        "\n".join(
            [
                "Intent: INT-8383",
                "## EVALUATION",
                "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
                "Priority Score: 7 /",
            ]
        ),
    ],
    ids=["missing-priority-line", "missing-justification"],
)
def test_validate_pr_body_fails_when_priority_line_invalid(body, capsys):
    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err
    assert "Error:" not in captured.err


@pytest.mark.parametrize("priority_line", INVALID_PRIORITY_LINES)
def test_main_blocks_pr_when_priority_line_invalid(priority_line, monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "load_forbidden_patterns", lambda _path: [])
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    body = _build_priority_body(priority_line)
    monkeypatch.setattr(
        check_governance_gate,
        "resolve_pr_body_with_source",
        lambda: (body, check_governance_gate.PR_BODY_SOURCE_NAME),
    )

    assert check_governance_gate.main() == 0
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err
    assert check_governance_gate.PR_BODY_SOURCE_NAME in captured.err
    assert "Error:" not in captured.err


def test_validate_pr_body_missing_intent(capsys):
    body = """
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 2 / SLO遵守
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Intent: INT-xxx" in captured.err
    assert "Error:" in captured.err


def test_main_allows_missing_intent(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setenv(
        "PR_BODY",
        """## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 2 / SLO遵守\n""",
    )
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Intent: INT-xxx" in captured.err
    assert f"{check_governance_gate.PR_BODY_SOURCE_NAME}:1" in captured.err
    assert "Error:" in captured.err


def test_validate_pr_body_missing_evaluation(capsys):
    body = """
Intent: INT-001
Priority Score: 3 / パフォーマンス改善
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Error:" in captured.err
    assert EVALUATION_SECTION_ERROR_MESSAGE in captured.err


def test_validate_pr_body_missing_evaluation_anchor(capsys):
    body = """
Intent: INT-001
## EVALUATION
Priority Score: 2 / 評価アンカー欠落
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Error:" in captured.err
    assert EVALUATION_SECTION_ERROR_MESSAGE in captured.err


def test_validate_pr_body_requires_evaluation_heading(capsys):
    body = """
Intent: INT-555
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Evaluation anchor is explained here without heading.
Priority Score: 1 / 評価見出し欠落
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Error:" in captured.err
    assert EVALUATION_SECTION_ERROR_MESSAGE in captured.err


@pytest.mark.parametrize(
    "body",
    [
        "\n".join(
            [
                "Intent: INT-9001",
                "Priority Score: 5 / 評価セクション欠落",
            ]
        ),
        "\n".join(
            [
                "Intent: INT-9002",
                "## EVALUATION",
                "Priority Score: 4 / 評価アンカー欠落",
            ]
        ),
        "\n".join(
            [
                "Intent: INT-9003",
                "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
                "Priority Score: 3 / 評価見出し欠落",
            ]
        ),
    ],
    ids=["missing-heading-and-anchor", "missing-anchor", "missing-heading"],
)
def test_main_blocks_pr_when_evaluation_section_incomplete(body, monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setenv("PR_BODY", body)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Error:" in captured.err
    assert EVALUATION_SECTION_ERROR_MESSAGE in captured.err
    assert check_governance_gate.PR_BODY_SOURCE_NAME in captured.err


def test_validate_pr_body_requires_priority_score(capsys):
    body = """
Intent: INT-789
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Priority Score" in captured.err
    assert "Acceptance Criteria" in captured.err


def test_main_fails_without_priority_score(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setenv(
        "PR_BODY",
        """Intent: INT-123\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\n""",
    )
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Priority Score" in captured.err
    assert "Acceptance Criteria" in captured.err
    assert "Error:" not in captured.err


def test_pr_template_contains_required_sections():
    template_path = Path(".github/PULL_REQUEST_TEMPLATE.md")
    if not template_path.exists():
        template_path = Path(".github/pull_request_template.md")
    template = template_path.read_text(encoding="utf-8")

    assert "Intent:" in template
    assert "## EVALUATION" in template
    assert "EVALUATION.md#acceptance-criteria" in template
    assert any(
        re.fullmatch(r"Priority Score[:：]\s*<[^>]+>\s*/\s*<[^>]+>", line.strip())
        for line in template.splitlines()
    ), "Priority Score line must follow 'Priority Score: <number> / <justification>' format"


def test_load_forbidden_patterns(tmp_path):
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """
self_modification:
  forbidden_paths:
    - "/core/schema/**"
    - '/auth/**'
    - "/core/schema/**"  # コメント付き
  require_human_approval:
    - "/governance/**"
"""
    )

    assert load_forbidden_patterns(policy) == [
        "core/schema/**",
        "auth/**",
        "core/schema/**",
    ]

    commented_policy = tmp_path / "policy_commented.yaml"
    commented_policy.write_text(
        """
self_modification:
  forbidden_paths:  # inline comment
    - "/core/schema/**"
"""
    )

    assert load_forbidden_patterns(commented_policy) == ["core/schema/**"]

    inline_policy = tmp_path / "policy_inline.yaml"
    inline_policy.write_text(
        """
self_modification:
  forbidden_paths: ["/core/schema/**", "/auth/**"]
"""
    )

    assert load_forbidden_patterns(inline_policy) == [
        "core/schema/**",
        "auth/**",
    ]

    inline_list_item_policy = tmp_path / "policy_inline_list_item.yaml"
    inline_list_item_policy.write_text(
        """
self_modification:
  forbidden_paths:
    - ["/core/schema/**", "/auth/**"]
"""
    )

    assert load_forbidden_patterns(inline_list_item_policy) == [
        "core/schema/**",
        "auth/**",
    ]


def test_collect_changed_paths_falls_back(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(list(args))
        refspec = args[-1]
        if refspec in {"origin/main...", "main..."}:
            raise check_governance_gate.subprocess.CalledProcessError(128, args)
        return type("Result", (), {"stdout": "first.txt\nsecond.txt\n"})()

    monkeypatch.setattr(check_governance_gate.subprocess, "run", fake_run)

    changed = check_governance_gate.collect_changed_paths()

    assert changed == ["first.txt", "second.txt"]
    assert calls == [
        ["git", "diff", "--name-only", "origin/main..."],
        ["git", "diff", "--name-only", "main..."],
        ["git", "diff", "--name-only", "HEAD"],
    ]


def test_main_accepts_pr_body_env(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setenv(
        "PR_BODY",
        """Intent: INT-999\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 2 / バグ修正優先\n""",
    )
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_accepts_pr_body_argument(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])

    exit_code = check_governance_gate.main(
        [
            "--pr-body",
            """Intent: INT-100\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 3 / 品質改善\n""",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_accepts_pr_body_file(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    pr_body_file = tmp_path / "body.md"
    pr_body_file.write_text(
        """Intent: INT-200\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 4 / セキュリティ向上\n""",
        encoding="utf-8",
    )

    exit_code = check_governance_gate.main([
        "--pr-body-file",
        str(pr_body_file),
    ])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_reports_priority_error_with_file_location(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    pr_body_file = tmp_path / "body.md"
    pr_body_file.write_text(
        """Intent: INT-300\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 3\n""",
        encoding="utf-8",
    )

    exit_code = check_governance_gate.main([
        "--pr-body-file",
        str(pr_body_file),
    ])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err
    assert f"Warning: {pr_body_file}:4:" in captured.err
    assert "Error:" not in captured.err


def test_main_reports_event_body_location(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.delenv("PR_BODY", raising=False)
    event_path = tmp_path / "event.json"
    body = """Intent: INT-400\n## EVALUATION\n- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)\nPriority Score: 3\n"""
    event_payload = {"pull_request": {"body": body}}
    event_path.write_text(json.dumps(event_payload), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err
    assert f"Warning: {event_path}:4:" in captured.err


def test_main_requires_pr_body(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.delenv("PR_BODY", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "PR body data is unavailable" in captured.err


def test_main_skips_for_non_pull_request_event(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setattr(check_governance_gate, "load_forbidden_patterns", lambda _path: [])
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Skipping governance gate" in captured.err


@pytest.mark.parametrize(
    "payload_updates",
    [
        {"pull_request": {"draft": True}},
        {"pull_request": {"base": {"ref": "release"}}, "repository": {"default_branch": "main"}},
    ],
)
def test_main_skips_for_draft_and_non_default_base(
    payload_updates, monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setattr(check_governance_gate, "load_forbidden_patterns", lambda _path: [])
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    payload = {"pull_request": {"body": "Intent: INT-1"}, "repository": {"default_branch": "main"}}
    payload = json.loads(json.dumps(payload))  # ensure copy
    for key, value in payload_updates.items():
        if isinstance(value, dict) and isinstance(payload.get(key), dict):
            payload[key].update(value)
        else:
            payload[key] = value
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    exit_code = check_governance_gate.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Skipping governance gate" in captured.err


def test_sample_pr_body_fixture_is_valid():
    sample_body_path = Path(
        "workflow-cookbook/tools/ci/fixtures/sample_pr_body.md"
    )
    body = sample_body_path.read_text(encoding="utf-8")

    assert check_governance_gate.validate_pr_body(body) is True
