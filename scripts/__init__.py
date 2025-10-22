"""Utility scripts for Day8 automation."""

from __future__ import annotations

import sys
from importlib import util
from pathlib import Path
from types import ModuleType

_ANALYZE_RELATIVE_PATH = Path("workflow-cookbook") / "scripts" / "analyze.py"


def _load_analyze_module() -> ModuleType:
    module_name = "scripts._workflow_cookbook_analyze"
    existing = sys.modules.get("scripts.analyze")
    if isinstance(existing, ModuleType):
        return existing

    module_path = Path(__file__).resolve().parents[1] / _ANALYZE_RELATIVE_PATH
    spec = util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load workflow-cookbook analyze script at {module_path}")
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    sys.modules["scripts.analyze"] = module
    return module


analyze = _load_analyze_module()

__all__ = ["analyze"]
