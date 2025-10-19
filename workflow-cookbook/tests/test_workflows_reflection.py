from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import textwrap
from collections.abc import Callable
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
        if: ${{ steps.artifact-locator.outputs.found == 'true' }}
        working-directory: workflow-cookbook
        run: |
          python scripts/analyze.py
    """.rstrip()

    assert expected_block in content


def test_reflection_workflow_analyze_step_requires_artifact() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() == "- name: Analyze logs → report":
            break
    else:  # pragma: no cover - defensive guard
        raise AssertionError("Analyze step not found")

    expected_condition = "        if: ${{ steps.artifact-locator.outputs.found == 'true' }}"

    assert expected_condition in lines[index + 1 : index + 4]


def test_reflection_workflow_commit_step_matches_analyze_condition() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    analyze_condition = _find_step_condition(lines, "- name: Analyze logs → report")
    determine_condition = _find_step_condition(lines, "- name: Determine reflection outputs")

    expected_condition = "        if: ${{ steps.artifact-locator.outputs.found == 'true' }}"

    assert analyze_condition == expected_condition
    assert determine_condition == expected_condition


def test_reflection_workflow_download_step_warns_when_artifact_missing() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_version_line = "        uses: actions/download-artifact@v4.1.7\n"
    fallback_notice = "core.notice(`test-logs artifact not found for run ${runId}; skipping download`);\n"
    cross_repo_notice = (
        "              core.notice(`run ${runId} belongs to ${repository}; cross-repo artifacts require a PAT with actions:read permissions.`);\n"
    )
    missing_repo_notice = (
        "              core.notice(`workflow_run repository unavailable; cross-repo artifacts require a PAT with actions:read permissions.`);\n"
    )
    download_name_line = "          name: test-logs\n"
    unexpected_artifact_id_reference = (
        "          artifact-id: ${{ steps.artifact-locator.outputs.artifact-id }}\n"
    )

    assert expected_version_line in content
    assert fallback_notice in content
    assert cross_repo_notice in content
    assert missing_repo_notice in content
    assert download_name_line in content
    assert unexpected_artifact_id_reference not in content
    assert "if-no-artifact-found" not in content


def test_reflection_workflow_download_step_extracts_to_workflow_directory() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    assert "          path: workflow-cookbook\n" in content
    assert "          path: .\n" not in content


def test_reflection_workflow_normalize_step_runs_in_workflow_directory() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() == "- name: Normalize downloaded log directories":
            break
    else:  # pragma: no cover - defensive guard
        raise AssertionError("Normalize step not found")

    assert "        working-directory: workflow-cookbook" in lines[index + 1 : index + 4]


def test_reflection_workflow_normalize_step_operates_on_logs_root() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_snippet = "\n".join(
        (
            "          if [ -d \"logs\" ]; then",
            "            shopt -s nullglob",
            "            for path in logs/*; do",
            "              if [ -d \"$path/logs\" ]; then",
            "                for entry in \"$path\"/logs/*; do",
            "                  name=\"$(basename \"$entry\")\"",
            "                  destination=\"$path/$name\"",
            "                  if [ -e \"$destination\" ]; then",
            "                    base=\"${name%.*}\"",
            "                    extension=\"\"",
            "                    if [ \"$base\" != \"$name\" ]; then",
            "                      extension=\".${name##*.}\"",
            "                    fi",
            "                    counter=1",
            "                    while [ -e \"$path/${base}-${counter}${extension}\" ]; do",
            "                      counter=$((counter + 1))",
            "                    done",
            "                    destination=\"$path/${base}-${counter}${extension}\"",
            "                  fi",
            "                  mv \"$entry\" \"$destination\"",
            "                done",
            "                rm -rf \"$path/logs\"",
            "              fi",
            "            done",
            "            shopt -u nullglob",
            "          fi",
        )
    )

    assert expected_snippet in content


def test_reflection_workflow_normalize_step_preserves_per_job_logs() -> None:
    run_block = _load_normalize_logs_run_block()

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        logs_root = temp_dir / "logs"
        (logs_root / "job-a" / "logs").mkdir(parents=True)
        (logs_root / "job-b" / "logs").mkdir(parents=True)

        (logs_root / "job-a" / "logs" / "test.jsonl").write_text("job-a", encoding="utf-8")
        (logs_root / "job-b" / "logs" / "test.jsonl").write_text("job-b", encoding="utf-8")

        subprocess.run(
            ["bash", "-c", textwrap.dedent(run_block)],
            check=True,
            cwd=temp_dir,
        )

        assert (logs_root / "job-a" / "test.jsonl").read_text(encoding="utf-8") == "job-a"
        assert (logs_root / "job-b" / "test.jsonl").read_text(encoding="utf-8") == "job-b"
        assert not (logs_root / "job-a" / "logs").exists()
        assert not (logs_root / "job-b" / "logs").exists()


def test_reflection_workflow_merge_step_updates_root_jsonl() -> None:
    run_block = _load_merge_logs_run_block()

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        logs_root = Path(temp_dir) / "logs"
        logs_root.mkdir()
        (logs_root / "test.jsonl").write_text("stale", encoding="utf-8")

        (logs_root / "job-a").mkdir()
        (logs_root / "job-b").mkdir()
        (logs_root / "job-a" / "alpha.jsonl").write_text("job-a", encoding="utf-8")
        (logs_root / "job-b" / "beta.jsonl").write_text("job-b", encoding="utf-8")

        subprocess.run(
            ["bash", "-c", textwrap.dedent(run_block)],
            check=True,
            cwd=temp_dir,
        )

        merged = (logs_root / "test.jsonl").read_text(encoding="utf-8")

        assert merged == "job-a\njob-b\n"
        assert "stale" not in merged


def test_reflection_workflow_merge_step_uses_recursive_jsonl_glob() -> None:
    run_block = _load_merge_logs_run_block()

    assert 'logs_dir.glob("**/*.jsonl")' in run_block


def test_reflection_workflow_merge_step_includes_nested_jsonl_files() -> None:
    run_block = _load_merge_logs_run_block()

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        logs_root = Path(temp_dir) / "logs"
        logs_root.mkdir()
        (logs_root / "test.jsonl").write_text("stale", encoding="utf-8")

        (logs_root / "job-a").mkdir()
        (logs_root / "job-a" / "nested").mkdir()
        (logs_root / "job-b").mkdir()
        (logs_root / "job-a" / "alpha.jsonl").write_text("alpha", encoding="utf-8")
        (logs_root / "job-a" / "nested" / "gamma.jsonl").write_text("gamma", encoding="utf-8")
        (logs_root / "job-b" / "beta.jsonl").write_text("beta", encoding="utf-8")

        subprocess.run(
            ["bash", "-c", textwrap.dedent(run_block)],
            check=True,
            cwd=temp_dir,
        )

        merged = (logs_root / "test.jsonl").read_text(encoding="utf-8")

        assert merged == "alpha\ngamma\nbeta\n"
        assert "stale" not in merged


def test_reflection_workflow_issue_step_uses_computed_issue_path() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    assert "      - name: Determine reflection outputs\n" in content
    assert "        id: reflection-paths\n" in content
    assert "          PYTHON_OUTPUT=\"$(python - <<'PY'" in content
    assert "              from scripts import analyze  # type: ignore\n" in content

    expected_if = (
        "        if: ${{ hashFiles(format('{0}', steps.reflection-paths.outputs.issue-hash-path)) != '0' }}\n"
    )
    expected_content_path = (
        "          content-filepath: ${{ steps.reflection-paths.outputs.issue-content-path }}\n"
    )

    assert expected_if in content
    assert expected_content_path in content
    assert "workflow-cookbook/logs/workflow-cookbook/logs" not in content


def test_reflection_workflow_defines_reflection_paths_step_id() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    workflow_content = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_content)

    assert isinstance(workflow, dict)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    reflect_job = jobs.get("reflect")
    assert isinstance(reflect_job, dict)
    steps = reflect_job.get("steps")
    if isinstance(steps, list):
        matching_steps = [
            step
            for step in steps
            if isinstance(step, dict) and step.get("id") == "reflection-paths"
        ]

        assert matching_steps, "reflection workflow must define id=reflection-paths step"
        return

    assert "        id: reflection-paths\n" in workflow_content


def test_reflection_workflow_issue_step_skips_when_file_missing() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    expected_condition = (
        "        if: ${{ hashFiles(format('{0}', steps.reflection-paths.outputs.issue-hash-path)) != '0' }}\n"
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
    condition_snippet = "hashFiles(format('{0}', steps.reflection-paths.outputs.issue-hash-path))"

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
    placeholder = "hashFiles(format('{0}', steps.reflection-paths.outputs.issue-hash-path))"

    assert expression.startswith(placeholder)
    simulated = expression.replace(placeholder, "'0'")

    assert simulated == "'0' != '0'"


def test_reflection_workflow_issue_step_uses_manifest_relative_path() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")

    assert "ISSUE_SUGGESTIONS_CONTENT_PATH" in content
    assert "ISSUE_SUGGESTIONS_HASH_PATH" in content
    assert "issue-content-path" in content
    assert "issue-hash-path" in content
    assert "content-filepath: ${{ steps.reflection-paths.outputs.issue-content-path }}\n" in content
    assert "read -r REPORT_PATH ISSUE_SUGGESTIONS_RELATIVE" in content


def _load_commit_run_block() -> str:
    return _load_reflection_paths_run_block()


def _extract_python_heredoc(run_block: str) -> str:
    lines = run_block.splitlines()
    script_lines: list[str] = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == "PYTHON_OUTPUT=\"$(python - <<'PY'":
            inside = True
            continue
        if inside and stripped == "PY":
            break
        if inside:
            script_lines.append(line)
    if not script_lines:
        raise AssertionError("Python heredoc not found in run block")

    script = textwrap.dedent("\n".join(script_lines))
    if not script.strip():  # pragma: no cover - defensive guard
        raise AssertionError("Python heredoc is empty")
    return script


def _load_normalize_logs_run_block() -> str:
    return _load_workflow_step_run_block("Normalize downloaded log directories")


def _load_merge_logs_run_block() -> str:
    return _load_workflow_step_run_block("Merge normalized test logs")


def _load_workflow_step_run_block(step_name: str) -> str:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "reflection.yml"
    )
    workflow_content = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_content)

    if isinstance(workflow, dict):
        jobs = workflow.get("jobs")
        if isinstance(jobs, dict):
            reflect_job = jobs.get("reflect")
            if isinstance(reflect_job, dict):
                steps = reflect_job.get("steps")
                if isinstance(steps, list):
                    for step in steps:
                        if isinstance(step, dict) and step.get("name") == step_name:
                            run_block = step.get("run")
                            assert isinstance(run_block, str)
                            return run_block

    lines = workflow_content.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line.strip() == f"- name: {step_name}":
            start_index = index
            break
    if start_index is None:  # pragma: no cover - defensive guard
        raise AssertionError(f"{step_name} step not found in workflow text")

    run_index = None
    for index in range(start_index + 1, len(lines)):
        if lines[index].strip() == "run: |":
            run_index = index
            break
    if run_index is None:  # pragma: no cover - defensive guard
        raise AssertionError(f"{step_name} run block missing in workflow text")

    base_indent = len(lines[run_index]) - len(lines[run_index].lstrip(" "))
    block_indent = None
    collected: list[str] = []
    for raw_line in lines[run_index + 1 :]:
        stripped = raw_line.strip()
        if stripped.startswith("- name:") and (len(raw_line) - len(raw_line.lstrip(" ")) <= base_indent):
            break
        if block_indent is None and stripped:
            block_indent = len(raw_line) - len(raw_line.lstrip(" "))
        if block_indent is not None:
            current_indent = len(raw_line) - len(raw_line.lstrip(" "))
            if stripped and current_indent < block_indent:
                break
            collected.append(raw_line)
    if not collected:  # pragma: no cover - defensive guard
        raise AssertionError(f"{step_name} run block empty")

    return "\n".join(collected)


def _load_reflection_paths_run_block() -> str:
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
        compute_step = next(
            step for step in steps if isinstance(step, dict) and step.get("name") == "Determine reflection outputs"
        )
        run_block = compute_step["run"]
        assert isinstance(run_block, str)
        return run_block

    lines = workflow_content.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line.strip() == "- name: Determine reflection outputs":
            start_index = index
            break
    if start_index is None:  # pragma: no cover - defensive guard
        raise AssertionError("Determine reflection outputs step not found in workflow text")

    run_index = None
    for index in range(start_index + 1, len(lines)):
        if lines[index].strip() == "run: |":
            run_index = index
            break
    if run_index is None:  # pragma: no cover - defensive guard
        raise AssertionError("Determine reflection outputs run block missing in workflow text")

    base_indent = len(lines[run_index]) - len(lines[run_index].lstrip(" "))
    block_indent = None
    collected: list[str] = []
    for raw_line in lines[run_index + 1 :]:
        stripped = raw_line.strip()
        if stripped.startswith("- name:") and (len(raw_line) - len(raw_line.lstrip(" ")) <= base_indent):
            break
        if block_indent is None and stripped:
            block_indent = len(raw_line) - len(raw_line.lstrip(" "))
        if block_indent is not None:
            collected.append(raw_line[block_indent:])
        else:
            collected.append("")
    if block_indent is None:  # pragma: no cover - defensive guard
        raise AssertionError("Determine reflection outputs run block content missing")

    return "\n".join(collected)


def test_reflection_workflow_commit_step_adds_report_output() -> None:
    run_block = _load_commit_run_block()

    assert "git config user.name \"reflect-bot\"" in run_block
    assert "git config user.email \"bot@example.com\"" in run_block
    assert "git add \"$REPORT_PATH\"" in run_block
    assert "git commit -m \"chore(report): reflection report [skip ci]\"" in run_block


def test_reflection_workflow_commit_step_git_add_matches_manifest_output() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "reflection.yaml"
    manifest_content = manifest_path.read_text(encoding="utf-8")
    manifest = yaml.safe_load(manifest_content)

    assert isinstance(manifest, dict)
    report_section = manifest["report"]
    assert isinstance(report_section, dict)
    expected_output = report_section["output"]
    assert isinstance(expected_output, str)

    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    stdout = io.StringIO()
    original_cwd = os.getcwd()
    try:
        os.chdir(repo_root)
        with contextlib.redirect_stdout(stdout):
            exec(python_script, {"__name__": "__main__"})
    finally:
        os.chdir(original_cwd)

    derived_lines = stdout.getvalue().splitlines()

    assert derived_lines[0] == expected_output
    assert derived_lines[1] == "reports/issue_suggestions.md"


def test_reflection_workflow_commit_step_fallback_strips_quotes() -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    namespace: dict[str, object] = {"__name__": "__fallback_test__"}
    exec(python_script, namespace)

    fallback = namespace.get("_fallback")
    assert isinstance(fallback, Callable)

    fallback_fn: Callable[[str], str] = fallback
    quoted_content = textwrap.dedent(
        """
        report:
          output: 'reports/today.md'
        """
    ).strip()

    result = fallback_fn(quoted_content)

    assert isinstance(result, str)
    assert result == "reports/today.md"


def test_reflection_workflow_commit_step_fallback_ignores_inline_comment() -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    namespace: dict[str, object] = {"__name__": "__fallback_test__"}
    exec(python_script, namespace)

    fallback = namespace.get("_fallback")
    assert isinstance(fallback, Callable)

    fallback_fn: Callable[[str], str] = fallback
    commented_content = textwrap.dedent(
        """
        report:
          output: "reports/daily.md"  # note
        """
    ).strip()

    result = fallback_fn(commented_content)

    assert isinstance(result, str)
    assert result == "reports/daily.md"


def test_reflection_workflow_commit_step_fallback_handles_commented_manifest_path() -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    namespace: dict[str, object] = {"__name__": "__fallback_test__"}
    exec(python_script, namespace)

    fallback = namespace.get("_fallback")
    assert isinstance(fallback, Callable)

    fallback_fn: Callable[[str], str] = fallback
    commented_content = textwrap.dedent(
        """
        report:
          output: "reports/today.md"  # note
        """
    ).strip()

    result = fallback_fn(commented_content)

    assert isinstance(result, str)
    assert result == "reports/today.md"


def test_reflection_workflow_commit_step_defaults_to_today_when_output_missing(tmp_path: Path) -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    temp_manifest = textwrap.dedent(
        """
        report:
          format: markdown
        """
    ).strip()

    manifest_path = tmp_path / "reflection.yaml"
    manifest_path.write_text(temp_manifest, encoding="utf-8")

    stdout = io.StringIO()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with contextlib.redirect_stdout(stdout):
            exec(python_script, {"__name__": "__main__"})
    finally:
        os.chdir(original_cwd)

    derived_lines = stdout.getvalue().splitlines()

    assert derived_lines[0] == "reports/today.md"
    assert derived_lines[1] == "reports/issue_suggestions.md"


def test_reflection_workflow_commit_step_aligns_issue_path_with_report_directory(tmp_path: Path) -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    temp_manifest = textwrap.dedent(
        """
        report:
          output: "reports/custom/out.md"
        """
    ).strip()

    manifest_path = tmp_path / "reflection.yaml"
    manifest_path.write_text(temp_manifest, encoding="utf-8")

    stdout = io.StringIO()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with contextlib.redirect_stdout(stdout):
            exec(python_script, {"__name__": "__main__"})
    finally:
        os.chdir(original_cwd)

    derived_lines = stdout.getvalue().splitlines()

    assert derived_lines[0] == "reports/custom/out.md"
    assert derived_lines[1] == "reports/custom/issue_suggestions.md"


def test_reflection_workflow_commit_step_rewrites_external_output_to_today(tmp_path: Path) -> None:
    run_block = _load_reflection_paths_run_block()
    python_script = _extract_python_heredoc(run_block)

    temp_manifest = textwrap.dedent(
        """
        report:
          output: "/tmp/outside.md"
        """
    ).strip()

    manifest_path = tmp_path / "reflection.yaml"
    manifest_path.write_text(temp_manifest, encoding="utf-8")

    stdout = io.StringIO()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with contextlib.redirect_stdout(stdout):
            exec(python_script, {"__name__": "__main__"})
    finally:
        os.chdir(original_cwd)

    derived_lines = stdout.getvalue().splitlines()

    assert derived_lines[0] == "reports/today.md"
    assert derived_lines[1] == "reports/issue_suggestions.md"
def _find_step_condition(lines: list[str], step_label: str) -> str:
    for index, line in enumerate(lines):
        if line.strip() == step_label:
            for candidate in lines[index + 1 :]:
                stripped = candidate.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("if: ${{") and stripped.endswith("}}"):
                    return candidate
                if stripped.startswith("-") and stripped.endswith(":"):
                    break
                if stripped.startswith("- name:"):
                    break
                if stripped.startswith("run:") or stripped.startswith("uses:"):
                    break
            raise AssertionError(f"{step_label} missing if condition")
    raise AssertionError(f"{step_label} not found")

