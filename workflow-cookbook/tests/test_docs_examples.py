from __future__ import annotations

from pathlib import Path


def _load_reflection_yaml_block() -> list[str]:
    doc_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "day8"
        / "examples"
        / "10_examples.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    prefix = "## reflection.yml（連動）\n```yaml\n"
    _, sep, remainder = content.partition(prefix)
    assert sep == prefix

    block, closing_sep, _ = remainder.partition("\n```")
    assert closing_sep == "\n```"

    return [line.rstrip() for line in block.splitlines()]


def test_reflection_example_includes_issue_steps() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "      - name: Determine reflection outputs" in yaml_lines
    assert "      - name: Open issue if needed" in yaml_lines


def test_reflection_example_exports_issue_paths_to_env() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert (
        "          echo \"ISSUE_CONTENT_PATH=$ISSUE_CONTENT_PATH\" >> \"$GITHUB_ENV\""
        in yaml_lines
    )
    assert (
        "          echo \"ISSUE_HASH_PATH=$ISSUE_HASH_PATH\" >> \"$GITHUB_ENV\""
        in yaml_lines
    )
    assert (
        "        if: ${{ hashFiles(format('{0}', env.ISSUE_HASH_PATH)) != '0' }}" in yaml_lines
    )
    assert (
        "          content-filepath: ${{ env.ISSUE_CONTENT_PATH }}" in yaml_lines
    )


def test_reflection_example_exports_report_path_to_env() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert (
        "          echo \"REPORT_PATH=$REPORT_PATH\" >> \"$GITHUB_ENV\"" in yaml_lines
    )


def test_reflection_example_stages_report_file() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          REPORT_PATH=\"reports/today.md\"" in yaml_lines
    assert "          git add \"$REPORT_PATH\"" in yaml_lines


def test_reflection_example_stage_uses_outputs_env() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "      - name: Stage reflection report" in yaml_lines
    assert "        env:" in yaml_lines
    assert (
        "          REPORT_PATH: ${{ steps.reflection-paths.outputs.report-path }}"
        in yaml_lines
    )


def test_reflection_example_does_not_stage_with_repo_prefix() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          git add workflow-cookbook/reports/today.md" not in yaml_lines


def test_reflection_download_artifact_path_is_repo_root() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          path: workflow-cookbook/logs" not in yaml_lines


def test_reflection_download_artifact_includes_run_id() -> None:
    yaml_lines = _load_reflection_yaml_block()

    assert "          run-id: ${{ github.event.workflow_run.id }}" in yaml_lines
