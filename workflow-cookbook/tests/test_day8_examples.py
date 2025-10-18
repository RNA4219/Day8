from __future__ import annotations

from pathlib import Path


def test_reflection_example_analyze_step_uses_repo_relative_command() -> None:
    doc_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "day8"
        / "examples"
        / "10_examples.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    expected_command = "python scripts/analyze.py"
    legacy_command = "python workflow-cookbook/scripts/analyze.py"

    assert expected_command in content
    assert legacy_command not in content
