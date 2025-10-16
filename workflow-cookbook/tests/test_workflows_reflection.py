from __future__ import annotations

from pathlib import Path

from test_workflows_defaults import yaml


def test_reflection_yaml_uses_repo_relative_paths() -> None:
    reflection_path = Path(__file__).resolve().parents[1] / "reflection.yaml"
    manifest = yaml.safe_load(reflection_path.read_text(encoding="utf-8"))

    assert isinstance(manifest, dict)

    report = manifest.get("report")
    assert isinstance(report, dict)

    output = report.get("output")
    assert isinstance(output, str)
    assert output == "reports/today.md"
    assert not output.startswith("../")

    raw_targets = manifest.get("targets")
    if isinstance(raw_targets, dict):
        converted_target: dict[str, object] = {}
        if "- name" in raw_targets:
            converted_target["name"] = raw_targets["- name"]
        if "logs" in raw_targets:
            converted_target["logs"] = raw_targets["logs"]
        targets: list[object] = [converted_target]
    else:
        targets = raw_targets

    assert isinstance(targets, list)
    first_target = targets[0]
    assert isinstance(first_target, dict)

    logs = first_target.get("logs")
    assert isinstance(logs, list)
    assert logs == ["logs/test.jsonl"]
    for log in logs:
        assert isinstance(log, str)
        assert not log.startswith("../")


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
