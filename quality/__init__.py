"""quality パッケージ."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import evaluator

if TYPE_CHECKING:  # pragma: no cover
    from . import pipeline

__all__ = ["pipeline", "evaluator"]
