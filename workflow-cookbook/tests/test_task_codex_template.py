from __future__ import annotations

from pathlib import Path


def test_task_template_requires_priority_score() -> None:
    project_root = Path(__file__).resolve().parents[1]
    template = project_root / "TASK.codex.md"

    content = template.read_text(encoding="utf-8")

    assert "Priority Score" in content, "TASK.codex.md の Deliverables で Priority Score を明示してください"
    assert (
        "Priority Score（必須）" in content
    ), "TASK.codex.md の Deliverables で Priority Score が必須であることを記載してください"
    assert (
        "Priority Score: <number> / <justification>" in content
    ), "TASK.codex.md に Priority Score の形式例 'Priority Score: <number> / <justification>' を含めてください"
