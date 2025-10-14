import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ci.check_governance_gate import (
    find_forbidden_matches,
    load_forbidden_patterns,
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
    is_valid, reason = validate_priority_score(body)
    assert is_valid is expected
    if expected:
        assert reason is None
    else:
        assert reason is not None
        if message is not None:
            assert message in reason


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
