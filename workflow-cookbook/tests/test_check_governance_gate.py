import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ci.check_governance_gate import (
    find_forbidden_matches,
    load_forbidden_patterns,
    main,
    validate_priority_score,
)


@pytest.mark.parametrize(
    "changed_paths, patterns, expected",
    [
        ("core/schema".splitlines(), ["/core/schema/**"], ["core/schema"]),
        ("""core/schema/model.yaml\ndocs/guide.md""".splitlines(), ["/core/schema/**"], ["core/schema/model.yaml"]),
        ("""docs/readme.md\nops/runbook.md""".splitlines(), ["/core/schema/**"], []),
        (
            """auth/service.py\ncore/schema/definitions.yml""".splitlines(),
            ["/auth/**", "/core/schema/**"],
            ["auth/service.py", "core/schema/definitions.yml"],
        ),
        (
            """core/schema/v1/model.yaml\nauth/service/internal/api.py""".splitlines(),
            ["/core/schema/**", "/auth/**"],
            ["core/schema/v1/model.yaml", "auth/service/internal/api.py"],  # normalized パス。現行ロジックでは検知できずテスト失敗を想定。
        ),
        (
            ["doc/config.yaml"],
            ["/docs/**"],
            [],
        ),
    ],
)
def test_find_forbidden_matches(changed_paths, patterns, expected):
    normalized = [pattern.lstrip("/") for pattern in patterns]
    assert find_forbidden_matches(changed_paths, normalized) == expected


def test_find_forbidden_matches_normalizes_patterns_and_paths():
    changed_paths = ["./auth", "auth\\service.py", "docs/readme.md"]
    patterns = ["/auth/**"]
    assert find_forbidden_matches(changed_paths, patterns) == ["auth", "auth/service.py"]


def test_find_forbidden_matches_handles_windows_style_patterns():
    changed_paths = ["auth/service.py"]
    patterns = [".\\auth\\**"]
    assert find_forbidden_matches(changed_paths, patterns) == ["auth/service.py"]


def test_find_forbidden_matches_preserves_result_order():
    changed_paths = ["./auth", "core/schema/model.yaml", "logs/system.log"]
    patterns = ["/auth/**", "/core/schema/**"]
    assert find_forbidden_matches(changed_paths, patterns) == [
        "auth",
        "core/schema/model.yaml",
    ]


@pytest.mark.parametrize(
    "body",
    [
        "- Priority Score: 7 / 箇条書き",
        "- [x] Priority Score: 8 / チェック済み",
    ],
)
def test_validate_priority_score_accepts_bullet_formats(body):
    is_valid, reason = validate_priority_score(body)
    assert is_valid is True
    assert reason is None


@pytest.mark.parametrize(
    "body, expected, message",
    [
        ("Priority Score: 5 / 安全性強化", True, None),
        ("Priority Score: 1 / 即応性向上", True, None),
        ("Priority Score: 3", False, "根拠"),
        ("Priority Score: / 理由", False, "数値"),
        ("Priority Score: abc / 理由", False, "数値"),
        (
            "Priority Score: <!-- 例: 5 / prioritization.yaml#phase1 -->",
            False,
            "数値",
        ),
        ("priority score: 3", False, "記載"),
        ("", False, "Priority Score"),
        (None, False, "Priority Score"),
    ],
)
def test_validate_priority_score(body, expected, message):
    is_valid, error = validate_priority_score(body)
    assert is_valid is expected
    if expected:
        assert error is None
    else:
        assert error is not None
        if message is not None:
            assert message in error


@pytest.mark.parametrize(
    "body",
    [
        "Priority Score: 5 / 安全性強化",
        "- Priority Score: 5 / 箇条書き",
        "* Priority Score: 7 / 別記号",
        "+ Priority Score: 9 / プラス記号",
        "- [ ] Priority Score: 4 / 未チェック",
        "- [x] Priority Score: 8 / チェック済み",
    ],
)
def test_validate_priority_score_valid(body):
    is_valid, error = validate_priority_score(body)
    assert is_valid is True
    assert error is None


def test_load_forbidden_patterns(tmp_path):
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """
self_modification:
  forbidden_paths:
    - "/core/schema/**"
    - '/auth/**'
  require_human_approval:
    - "/governance/**"
"""
    )

    assert load_forbidden_patterns(policy) == ["core/schema/**", "auth/**"]


def test_load_forbidden_patterns_ignores_inline_comments(tmp_path):
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """
self_modification:
  forbidden_paths:
    - "/core/schema/**"  # コメント付き
  require_human_approval:
    - "/governance/**"
"""
    )

    assert load_forbidden_patterns(policy) == ["core/schema/**"]


def test_main_returns_error_when_priority_score_invalid(tmp_path, monkeypatch, capsys):
    from tools.ci import check_governance_gate as module

    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"body": "Priority Score: invalid"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr(module, "get_changed_paths", lambda refspec: [])
    def stub_validate_priority_score(body: str | None) -> tuple[bool, str | None]:
        return False, "Priority Score validation failed"

    monkeypatch.setattr(module, "validate_priority_score", stub_validate_priority_score)

    exit_code = module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Priority Score validation failed" in captured.err
