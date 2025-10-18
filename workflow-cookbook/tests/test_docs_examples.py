from __future__ import annotations

from pathlib import Path


def _load_reflection_yaml_block() -> list[str]:
    doc_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "day8"
        / "examples"
        / "10_examples.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    prefix = "## reflection.yml（連動）\n```yaml\n"
    _, sep, remainder = content.partition(prefix)
    assert sep == prefix

    block, closing_sep, _ = remainder.partition("\n```")
    assert closing_sep == "\n```"

    return [line.rstrip() for line in block.splitlines()]


def test_reflection_example_stages_report_file() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          git add reports/today.md" in yaml_lines


def test_reflection_example_does_not_stage_with_repo_prefix() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          git add workflow-cookbook/reports/today.md" not in yaml_lines
