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
        ("""core/schema/model.yaml\ndocs/guide.md""".splitlines(), ["/core/schema/**"], ["core/schema/model.yaml"]),
        ("""docs/readme.md\nops/runbook.md""".splitlines(), ["/core/schema/**"], []),
        (
            """auth/service.py\ncore/schema/definitions.yml""".splitlines(),
            ["/auth/**", "/core/schema/**"],
            ["auth/service.py", "core/schema/definitions.yml"],
        ),
    ],
)
def test_find_forbidden_matches(changed_paths, patterns, expected):
    normalized = [pattern.lstrip("/") for pattern in patterns]
    assert find_forbidden_matches(changed_paths, normalized) == expected


@pytest.mark.parametrize(
    "body, expected",
    [
        ("Priority Score: 5 / 安全性強化", True),
        ("前文\nPriority Score: 1 / 即応性向上\n後文", True),
        ("Priority Score: 3", False),
        ("Priority Score: / 理由", False),
        ("Priority Score: abc / 理由", False),
        ("Priority Score: <!-- 例: 5 / prioritization.yaml#phase1 -->", False),
        ("priority score: 3 / something", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_priority_score_table(body, expected):
    assert validate_priority_score(body) is expected
    error = getattr(validate_priority_score, "error", None)
    if expected:
        assert error is None
    else:
        assert isinstance(error, str)


@pytest.mark.parametrize(
    "body",
    [
        "Priority Score: 5 / 安全性強化",
        "- Priority Score: 5 / 例示",
        "- [x] Priority Score: 8 / チェック済み",
    ],
)
def test_validate_priority_score_valid(body):
    assert validate_priority_score(body) is True


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


def test_main_returns_error_when_priority_score_invalid(tmp_path, monkeypatch, capsys):
    from tools.ci import check_governance_gate as module

    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"body": "Priority Score: invalid"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr(module, "get_changed_paths", lambda refspec: [])
    monkeypatch.setattr(module, "validate_priority_score", lambda body: False)

    exit_code = module.main()
    captured = capsys.readouterr()

    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr("tools.ci.check_governance_gate.get_changed_paths", lambda _ref: [])
    monkeypatch.setattr("tools.ci.check_governance_gate.validate_priority_score", fake_validate)

    assert main() == 1
    captured = capsys.readouterr()
    assert "Priority score validation failed" in captured.err
    assert "Priority Score value must be a number" in captured.err
