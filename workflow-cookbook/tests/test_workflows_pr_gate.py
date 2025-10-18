from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_workflows_defaults_module() -> ModuleType:
    module_path = Path(__file__).with_name("test_workflows_defaults.py")
    spec = importlib.util.spec_from_file_location(
        "workflow_cookbook.tests.test_workflows_defaults", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_yaml_loader(module: ModuleType) -> Any:
    yaml_loader = getattr(module, "yaml", None)
    assert yaml_loader is not None, "yaml ローダーが見つかりません"
    safe_load = getattr(yaml_loader, "safe_load", None)
    assert callable(safe_load), "yaml.safe_load が必要です"
    return yaml_loader


_DEF_MODULE = _load_workflows_defaults_module()
_YAML = _load_yaml_loader(_DEF_MODULE)


def test_pr_gate_runs_governance_gate() -> None:
    workflow_path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pr_gate.yml"
    workflow_yaml = workflow_path.read_text(encoding="utf-8")

    workflow = _YAML.safe_load(workflow_yaml)
    assert isinstance(workflow, dict), "ワークフローはマップ形式である必要があります"

    after_checkout = False
    governance_gate_found = False

    for line in workflow_yaml.splitlines():
        stripped = line.strip()
        if stripped.startswith("- uses: actions/checkout@"):
            after_checkout = True
            continue
        if after_checkout and "python workflow-cookbook/tools/ci/check_governance_gate.py" in stripped:
            governance_gate_found = True
            break

    assert after_checkout, "actions/checkout ステップが必要です"
    assert (
        governance_gate_found
    ), "checkout 後に python workflow-cookbook/tools/ci/check_governance_gate.py を実行するステップが必要です"
