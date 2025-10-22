"""requirements-eval.txt の依存関係を検証するテスト。"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Iterable


def _iter_requirement_names(lines: Iterable[str]) -> set[str]:
    entries: set[str] = set()
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        requirement_name = stripped.split("==", 1)[0].strip().lower()
        entries.add(requirement_name)
    return entries


def test_requirements_eval_contains_beautifulsoup4() -> None:
    requirements_path = Path("requirements-eval.txt")
    names = _iter_requirement_names(requirements_path.read_text(encoding="utf-8").splitlines())
    assert "beautifulsoup4" in names, "requirements-eval.txt に beautifulsoup4 を追加してください"


def test_bs4_can_be_imported() -> None:
    import_module("bs4")
