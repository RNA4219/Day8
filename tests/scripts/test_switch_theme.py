from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.switch_theme import ThemeNotFoundError, main


def _prepare_theme(project_root: Path, theme_name: str, content: dict[str, str]) -> None:
    themes_dir = project_root / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    (themes_dir / f"{theme_name}.theme.json").write_text(
        json.dumps(content),
        encoding="utf-8",
    )


def test_main_copies_requested_theme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path
    _prepare_theme(project_root, "mocha", {"name": "mocha"})
    public_dir = project_root / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.chdir(project_root)

    exit_code = main(["mocha"])

    assert exit_code == 0
    target_path = public_dir / "theme.json"
    assert target_path.exists()
    assert json.loads(target_path.read_text(encoding="utf-8")) == {"name": "mocha"}


def test_main_fails_when_theme_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path
    (project_root / "themes").mkdir(parents=True, exist_ok=True)
    (project_root / "public").mkdir(parents=True, exist_ok=True)

    monkeypatch.chdir(project_root)

    with pytest.raises(SystemExit) as excinfo:
        main(["unknown"])

    assert excinfo.value.code == "Theme not found: unknown"

    with pytest.raises(ThemeNotFoundError):
        raise excinfo.value.__cause__
