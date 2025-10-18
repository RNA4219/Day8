from __future__ import annotations

from pathlib import Path


def test_readme_priority_score_is_mandatory() -> None:
    project_root = Path(__file__).resolve().parents[1]
    readme = project_root / "README.md"

    content = readme.read_text(encoding="utf-8")

    assert "Priority Score" in content, "README.md には Priority Score を要求するチェック項目が必要です"
    assert "必ず" in content, "README.md のチェックリストで Priority Score が必須である旨を明記してください"
    assert (
        "<number> / <justification>" in content
    ), "README.md には Priority Score の形式例として '<number> / <justification>' を含めてください"
