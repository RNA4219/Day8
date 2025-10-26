# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 RNA4219

from __future__ import annotations

import os
import sys
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence, cast


_SAMPLE_FLAG = "--use-sample-pr-body"
_SAMPLE_RELATIVE_PATH = Path("workflow-cookbook") / "tools" / "ci" / "fixtures" / "sample_pr_body.md"
_LEGACY_SCRIPT_RELATIVE_PATH = Path("workflow-cookbook") / "tools" / "ci" / "check_governance_gate.py"
_PR_EVENT_NAMES = {"pull_request", "pull_request_target"}
_PR_EVENT_ENVIRONMENT_VARIABLES: tuple[str, ...] = (
    "GITHUB_EVENT_PATH",
    "GITHUB_EVENT_NAME",
)


_legacy_module: ModuleType | None = None
_PROXY_ATTRIBUTE_NAMES = {
    "collect_changed_paths",
    "load_forbidden_patterns",
    "resolve_pr_body_with_source",
    "REPO_ROOT_NAME",
}
_BASELINE_ATTRIBUTES: dict[str, object] = {}


def _prepare_arguments(argv: Sequence[str] | None) -> tuple[list[str], bool]:
    if argv is None:
        argv = ()
    filtered: list[str] = []
    use_sample = False
    for argument in argv:
        if argument == _SAMPLE_FLAG:
            use_sample = True
            continue
        filtered.append(argument)
    return filtered, use_sample


def _load_sample_body(sample_path: Path) -> str:
    return sample_path.read_text(encoding="utf-8")


def _should_use_sample(use_sample_flag: bool) -> bool:
    if use_sample_flag:
        return True
    if os.environ.get("PR_BODY"):
        return False
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return True
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name is None:
        return False
    return event_name not in _PR_EVENT_NAMES


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_legacy_script() -> Path:
    repo_root = _resolve_repo_root()
    legacy_script = repo_root / _LEGACY_SCRIPT_RELATIVE_PATH
    if not legacy_script.is_file():
        raise FileNotFoundError(legacy_script)
    return legacy_script


def _load_legacy_module() -> ModuleType:
    global _legacy_module
    if _legacy_module is None:
        legacy_script = _resolve_legacy_script()
        spec = util.spec_from_file_location(
            "workflow_cookbook.tools.ci.check_governance_gate",
            legacy_script,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load governance gate module at {legacy_script}")
        module = util.module_from_spec(spec)
        loader = spec.loader
        assert loader is not None
        sys.modules[spec.name] = module
        try:
            loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _legacy_module = module
    return _legacy_module


def _expose_attribute(name: str) -> Any:
    legacy = _load_legacy_module()
    value = getattr(legacy, name)
    globals()[name] = value
    _BASELINE_ATTRIBUTES.setdefault(name, value)
    return value


def __getattr__(name: str) -> Any:
    try:
        value = _expose_attribute(name)
    except AttributeError as exc:  # pragma: no cover - mirrors Python behaviour
        raise AttributeError(name) from exc
    return value


load_forbidden_patterns = _expose_attribute("load_forbidden_patterns")
find_forbidden_matches = _expose_attribute("find_forbidden_matches")
validate_pr_body = _expose_attribute("validate_pr_body")
REPO_ROOT_NAME = _expose_attribute("REPO_ROOT_NAME")
PRIORITY_SCORE_ERROR_MESSAGE = _expose_attribute("PRIORITY_SCORE_ERROR_MESSAGE")


def _synchronize_proxy_attributes(legacy: ModuleType) -> None:
    for name in _PROXY_ATTRIBUTE_NAMES:
        if name in globals():
            value = globals()[name]
            baseline = _BASELINE_ATTRIBUTES.get(name)
            if baseline is None:
                baseline = getattr(legacy, name, None)
                if baseline is not None:
                    _BASELINE_ATTRIBUTES[name] = baseline
            setattr(legacy, name, value)


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = _resolve_repo_root()
    _resolve_legacy_script()

    filtered_args, use_sample_flag = _prepare_arguments(argv)

    should_apply_sample = argv is not None and _should_use_sample(use_sample_flag)
    if should_apply_sample:
        sample_path = repo_root / _SAMPLE_RELATIVE_PATH
        if not sample_path.is_file():
            raise FileNotFoundError(sample_path)
        sample_body = _load_sample_body(sample_path)
        os.environ["PR_BODY"] = sample_body
        for variable in _PR_EVENT_ENVIRONMENT_VARIABLES:
            os.environ.pop(variable, None)

    legacy = _load_legacy_module()
    _synchronize_proxy_attributes(legacy)
    legacy_main = cast(Any, getattr(legacy, "main", None))
    if legacy_main is None:
        raise AttributeError("main")
    forwarded_args: Sequence[str] | None
    if argv is None:
        forwarded_args = None
    else:
        forwarded_args = tuple(filtered_args)
    return int(legacy_main(forwarded_args))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
