"""requirements-eval.txt の依存関係を検証するテスト。"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path


def test_requirements_eval_contains_beautifulsoup4() -> None:
    requirements_path = Path("requirements-eval.txt")
    contents = requirements_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in contents.splitlines() if line.strip() and not line.startswith("#")]
    assert any(line.split("==")[0] == "beautifulsoup4" for line in lines), "requirements-eval.txt に beautifulsoup4 を追加してください"


def test_bs4_can_be_imported() -> None:
    import_module("bs4")
