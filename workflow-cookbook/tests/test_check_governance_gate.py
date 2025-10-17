import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ci import check_governance_gate
from tools.ci.check_governance_gate import (
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


def test_validate_pr_body_rejects_priority_without_justification(capsys):
    body = """
Intent: INT-777
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 3
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert (
        "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
        in captured.err
    )


@pytest.mark.parametrize(
    "priority_line",
    [
        "",
        "Priority Score:",
        "Priority Score: 4",
        "Priority Score: 4 /",
        "Priority Score: 4 /   ",
    ],
)
def test_validate_pr_body_rejects_missing_priority_details(priority_line, capsys):
    lines = [
        "Intent: INT-4242",
        "## EVALUATION",
        "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
    ]
    if priority_line:
        lines.append(priority_line)
    body = "\n".join(lines)

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert (
        "Priority Score must be provided as '<number> / <justification>' to reflect Acceptance Criteria prioritization"
        in captured.err
    )


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
    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err


@pytest.mark.parametrize(
    "body",
    [
        "\n".join(
            [
                "Intent: INT-9000",
                "## EVALUATION",
                "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
            ]
        ),
        "\n".join(
            [
                "Intent: INT-4242",
                "## EVALUATION",
                "- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)",
                "Priority Score: 2 /",
            ]
        ),
    ],
    ids=["missing-priority-line", "missing-justification"],
)
def test_main_blocks_pr_when_priority_line_invalid(body, monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "load_forbidden_patterns", lambda _path: [])
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.setattr(check_governance_gate, "resolve_pr_body", lambda: body)

    assert check_governance_gate.main() == 1
    captured = capsys.readouterr()
    assert PRIORITY_SCORE_ERROR_MESSAGE in captured.err


def test_validate_pr_body_missing_intent(capsys):
    body = """
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Priority Score: 2 / SLO遵守
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR body must include 'Intent: INT-xxx'" in captured.err


def test_validate_pr_body_missing_evaluation(capsys):
    body = """
Intent: INT-001
Priority Score: 3 / パフォーマンス改善
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR must reference EVALUATION (acceptance) anchor" in captured.err


def test_validate_pr_body_missing_evaluation_anchor(capsys):
    body = """
Intent: INT-001
## EVALUATION
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR must reference EVALUATION (acceptance) anchor" in captured.err


def test_validate_pr_body_requires_evaluation_heading(capsys):
    body = """
Intent: INT-555
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
Evaluation anchor is explained here without heading.
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR must reference EVALUATION (acceptance) anchor" in captured.err


def test_validate_pr_body_requires_priority_score(capsys):
    body = """
Intent: INT-789
## EVALUATION
- [Acceptance Criteria](../EVALUATION.md#acceptance-criteria)
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
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

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Priority Score" in captured.err
    assert "Acceptance Criteria" in captured.err


def test_pr_template_contains_required_sections():
    template_path = Path(".github/PULL_REQUEST_TEMPLATE.md")
    if not template_path.exists():
        template_path = Path(".github/pull_request_template.md")
    template = template_path.read_text(encoding="utf-8")

    assert "Intent:" in template
    assert "## EVALUATION" in template
    assert "EVALUATION.md#acceptance-criteria" in template


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


def test_main_requires_pr_body(monkeypatch, capsys):
    monkeypatch.setattr(check_governance_gate, "collect_changed_paths", lambda: [])
    monkeypatch.delenv("PR_BODY", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    exit_code = check_governance_gate.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "PR body data is unavailable" in captured.err
