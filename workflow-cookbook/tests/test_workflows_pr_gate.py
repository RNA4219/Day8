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

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "jobs 定義が必要です"

    gate_job = jobs.get("gate")
    assert isinstance(gate_job, dict), "gate ジョブ定義が必要です"

    steps = gate_job.get("steps")
    if isinstance(steps, list):
        checkout_index: int | None = None
        checkout_step: dict[str, Any] | None = None
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/checkout@"):
                checkout_index = index
                checkout_step = step
                break

        assert checkout_index is not None, "actions/checkout ステップが必要です"
        checkout_with = checkout_step.get("with") if isinstance(checkout_step, dict) else None
        fetch_depth = None
        if isinstance(checkout_with, dict):
            fetch_depth = checkout_with.get("fetch-depth")
        assert fetch_depth in {0, "0"}, "checkout には fetch-depth: 0 が必要です"

        setup_python_found = False
        python_version_valid = False
        governance_gate_found = False
        for step in steps[checkout_index + 1 :]:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.lower() == "actions/setup-python@v5":
                setup_python_found = True
                with_section = step.get("with")
                python_version = (
                    with_section.get("python-version")
                    if isinstance(with_section, dict)
                    else None
                )
                python_version_valid = python_version in {"3.11", 3.11}
                continue
            run = step.get("run")
            if isinstance(run, str) and "python workflow-cookbook/tools/ci/check_governance_gate.py" in run:
                governance_gate_found = True
                break

        assert setup_python_found, "actions/setup-python@v5 ステップが必要です"
        assert python_version_valid, "Python 3.11 をセットアップする必要があります"
        assert (
            governance_gate_found
        ), "checkout 後に python workflow-cookbook/tools/ci/check_governance_gate.py を実行するステップが必要です"
        return

    assert isinstance(steps, dict), "steps 配列またはマップが必要です"

    after_checkout = False
    fetch_depth_found = False
    setup_python_found = False
    python_version_valid = False
    governance_gate_found = False
    for line in workflow_yaml.splitlines():
        stripped = line.strip()
        if stripped.startswith("- uses: actions/checkout@"):
            after_checkout = True
            continue
        if after_checkout and stripped.startswith("fetch-depth:"):
            fetch_depth_found = stripped.split(":", 1)[1].strip().strip('"\'') == "0"
            continue
        if after_checkout and "python workflow-cookbook/tools/ci/check_governance_gate.py" in stripped:
            governance_gate_found = True
            break
        if after_checkout and stripped.startswith("- name: Setup Python"):
            setup_python_found = True
            continue
        if setup_python_found and stripped.startswith("uses: actions/setup-python@v5"):
            continue
        if setup_python_found and stripped.startswith("python-version:"):
            python_version_valid = "3.11" in stripped
            continue

    assert after_checkout, "actions/checkout ステップが必要です"
    assert fetch_depth_found, "checkout には fetch-depth: 0 が必要です"
    assert setup_python_found, "actions/setup-python@v5 ステップが必要です"
    assert python_version_valid, "Python 3.11 をセットアップする必要があります"
    assert (
        governance_gate_found
    ), "checkout 後に python workflow-cookbook/tools/ci/check_governance_gate.py を実行するステップが必要です"
