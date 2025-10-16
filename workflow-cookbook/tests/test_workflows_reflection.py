from __future__ import annotations

from pathlib import Path


def test_reflection_yaml_uses_repo_relative_paths() -> None:
    reflection_path = Path(__file__).resolve().parents[1] / "reflection.yaml"
    content = reflection_path.read_text(encoding="utf-8")

    assert "logs/test.jsonl" in content
    assert "../logs/test.jsonl" not in content
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

    expected_block = (
        "\n".join(
            [
                "      - name: Analyze logs → report",
                "        working-directory: workflow-cookbook",
                "        run: |",
                "          python scripts/analyze.py",
            ]
        )
        + "\n"
    )

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
