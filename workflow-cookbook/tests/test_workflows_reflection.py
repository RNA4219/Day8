from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
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


def test_reflection_workflow_issue_step_condition_checks_hashfiles_zero() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    condition_snippet = "hashFiles('workflow-cookbook/reports/issue_suggestions.md')"

    assert f"{condition_snippet} != '0'" in content
    assert f"{condition_snippet} != ''" not in content


def test_reflection_workflow_issue_step_condition_evaluates_false_when_missing() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() == "- name: Open issue if needed (draft memo)":
            break
    else:  # pragma: no cover - defensive guard
        raise AssertionError("Issue creation step not found")

    condition_line = ""
    for candidate in lines[index + 1 :]:
        stripped = candidate.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("if: ${{") and stripped.endswith("}}"):  # expected format
            condition_line = stripped
            break
    else:  # pragma: no cover - defensive guard
        raise AssertionError("Issue creation step missing if condition")

    prefix = "if: ${{"
    suffix = "}}"
    expression = condition_line[len(prefix) : -len(suffix)].strip()
    placeholder = "hashFiles('workflow-cookbook/reports/issue_suggestions.md')"

    assert expression.startswith(placeholder)
    simulated = expression.replace(placeholder, "'0'")

    assert simulated == "'0' != '0'"


def test_reflection_workflow_commit_step_adds_report_output() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "reflection.yaml"
    manifest_content = manifest_path.read_text(encoding="utf-8")
    manifest = yaml.safe_load(manifest_content)

    assert isinstance(manifest, dict)
    report_section = manifest["report"]
    assert isinstance(report_section, dict)
    expected_output = report_section["output"]
    assert isinstance(expected_output, str)

    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    workflow_content = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_content)

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    reflect_job = jobs["reflect"]
    assert isinstance(reflect_job, dict)
    steps = reflect_job["steps"]
    if isinstance(steps, list):
        commit_step = next(
            step for step in steps if isinstance(step, dict) and step.get("name") == "Commit report"
        )
        run_block = commit_step["run"]
        assert isinstance(run_block, str)
    else:
        lines = workflow_content.splitlines()
        start_index = None
        for index, line in enumerate(lines):
            if line.strip() == "- name: Commit report":
                start_index = index
                break
        if start_index is None:  # pragma: no cover - defensive guard
            raise AssertionError("Commit report step not found in workflow text")

        run_index = None
        for index in range(start_index + 1, len(lines)):
            if lines[index].strip() == "run: |":
                run_index = index
                break
        if run_index is None:  # pragma: no cover - defensive guard
            raise AssertionError("Commit report run block missing in workflow text")

        base_indent = len(lines[run_index]) - len(lines[run_index].lstrip(" "))
        block_indent = None
        collected: list[str] = []
        for raw_line in lines[run_index + 1 :]:
            stripped = raw_line.strip()
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if stripped and indent <= base_indent:
                break
            if stripped and block_indent is None:
                block_indent = indent
            if block_indent is not None and stripped:
                collected.append(raw_line[block_indent:])
            else:
                collected.append("")
        if block_indent is None:  # pragma: no cover - defensive guard
            raise AssertionError("Commit report run block content missing")

        run_block = "\n".join(collected)

    lines = run_block.splitlines()

    match = re.search(r"python -c '(?P<code>.*)'\)\"", run_block, re.DOTALL)
    if match is None:  # pragma: no cover - defensive guard
        raise AssertionError("Unable to extract python code from command substitution")

    snippet = match.group("code")
    assert "reflection.yaml" in snippet
    stdout = io.StringIO()
    original_cwd = os.getcwd()
    try:
        os.chdir(repo_root)
        with contextlib.redirect_stdout(stdout):
            exec(snippet, {})
    finally:
        os.chdir(original_cwd)
    derived_output = stdout.getvalue().strip()

    assert derived_output == expected_output
    assert any(line.strip() == 'git add "$REPORT_PATH"' for line in lines)
