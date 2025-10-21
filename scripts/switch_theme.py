from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

THEME_EXTENSION = ".theme.json"
TARGET_FILENAME = "theme.json"


class ThemeSwitchError(RuntimeError):
    """Base exception for theme switching failures."""


class ThemeNotFoundError(ThemeSwitchError):
    """Raised when the requested theme file does not exist."""

    def __init__(self, theme_name: str) -> None:
        super().__init__(f"Theme not found: {theme_name}")
        self.theme_name = theme_name


def _resolve_project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root
    return Path.cwd()


def copy_theme(theme_name: str, project_root: Path | None = None) -> Path:
    project_root_path = _resolve_project_root(project_root)
    source = project_root_path / "themes" / f"{theme_name}{THEME_EXTENSION}"
    if not source.exists():
        raise ThemeNotFoundError(theme_name)

    destination = project_root_path / "public" / TARGET_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Switch the active Day8 theme.")
    parser.add_argument("theme_name", help="Name of the theme to activate.")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        copy_theme(args.theme_name)
    except ThemeSwitchError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
