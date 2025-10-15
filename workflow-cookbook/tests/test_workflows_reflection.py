from __future__ import annotations

from pathlib import Path


def test_reflection_workflow_analyze_step_runs_analyze_script() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_block = (
        "      - name: Analyze logs → report\n"
        "        working-directory: workflow-cookbook\n"
        "        run: |\n"
        "          python scripts/analyze.py\n"
    )

    assert expected_block in content
