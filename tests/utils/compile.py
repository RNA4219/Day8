"""Compilation helpers for smoke tests."""

from __future__ import annotations

import compileall
from pathlib import Path
from typing import Iterable, Sequence


class CompilationError(AssertionError):
    """Raised when a module fails to compile."""


def _coerce_paths(paths: Iterable[Path | str]) -> list[Path]:
    return [Path(path) for path in paths]


def assert_modules_compile(paths: Iterable[Path | str]) -> None:
    """Assert that the given Python source files compile without syntax errors."""

    resolved: Sequence[Path] = _coerce_paths(paths)
    missing = [path for path in resolved if not path.exists()]
    if missing:
        missing_str = ", ".join(str(path) for path in missing)
        raise CompilationError(f"Source files not found: {missing_str}")

    failures = [
        path
        for path in resolved
        if not compileall.compile_file(str(path), quiet=1, force=False)
    ]
    if failures:
        failed_str = ", ".join(str(path) for path in failures)
        raise CompilationError(f"Failed to compile: {failed_str}")

