from __future__ import annotations

import re
from pathlib import Path


def test_reflection_example_uses_repo_relative_git_add() -> None:
    doc_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "day8"
        / "examples"
        / "10_examples.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    reflection_section = re.search(
        r"## reflection\.yml（連動）\n```yaml\n(?P<block>.*?)```",
        content,
        re.DOTALL,
    )
    assert reflection_section is not None

    yaml_block = reflection_section.group("block")

    assert "git add reports/today.md" in yaml_block
    assert "git add workflow-cookbook/reports/today.md" not in yaml_block
