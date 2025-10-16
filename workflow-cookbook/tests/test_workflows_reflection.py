from __future__ import annotations

import importlib.util
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for test envs without PyYAML
    spec = importlib.util.spec_from_file_location(
        "workflow_cookbook.tests.test_workflows_defaults",
        Path(__file__).with_name("test_workflows_defaults.py"),
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise ImportError("Failed to load YAML fallback")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type, union-attr]
    yaml = module.yaml  # type: ignore[attr-defined]


def test_reflection_yaml_uses_repo_relative_paths() -> None:
    reflection_path = Path(__file__).resolve().parents[1] / "reflection.yaml"
    content = reflection_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    assert isinstance(data, dict)
    targets_data = data["targets"]
    if isinstance(targets_data, dict):
        normalized_target = {}
        if "- name" in targets_data:
            normalized_target["name"] = targets_data["- name"]
        for key, value in targets_data.items():
            if key == "- name":
                continue
            normalized_target[key] = value
        targets = [normalized_target]
    else:
        targets = targets_data

    assert isinstance(targets, list)
    logs = targets[0]["logs"]

    assert logs == ["logs/test.jsonl"]
    assert not any(path.startswith("..") for path in logs)
    assert "reports/today.md" in content
    assert "../reports/today.md" not in content


def test_reflection_workflow_analyze_step_runs_analyze_script() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_block = """\
      - name: Analyze logs → report
        working-directory: workflow-cookbook
        run: |
          python scripts/analyze.py
    """.rstrip()

    assert expected_block in content


def test_reflection_workflow_download_step_warns_when_artifact_missing() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_line = "          if-no-artifact-found: warn\n"

    assert expected_line in content


def test_reflection_workflow_issue_step_skips_when_file_missing() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_condition = (
        "        if: ${{ hashFiles('workflow-cookbook/reports/issue_suggestions.md') != '0' }}\n"
    )

    assert expected_condition in content
