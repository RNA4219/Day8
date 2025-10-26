"""Integration tests for the repository-level governance gate wrapper."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_wrapper_uses_sample_body_by_default() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_wrapper_overrides_existing_pr_body_with_sample() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    env = os.environ.copy()
    env.update({"PR_BODY": "bad body"})

    result = subprocess.run(
        [sys.executable, str(script), "--use-sample-pr-body"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr.strip() == ""


def test_wrapper_replaces_preset_pr_body_contents() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sample_path = repo_root / "workflow-cookbook" / "tools" / "ci" / "fixtures" / "sample_pr_body.md"
    sample_body = sample_path.read_text(encoding="utf-8")

    python_code = (
        "import os, sys\n"
        "from tools.ci import check_governance_gate as module\n"
        "os.environ['PR_BODY'] = 'bad body'\n"
        "exit_code = module.main(['--use-sample-pr-body'])\n"
        "sys.stdout.write(os.environ['PR_BODY'])\n"
        "sys.exit(exit_code)\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", python_code],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == sample_body


def test_wrapper_ignores_pr_event_when_using_sample() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    env = os.environ.copy()
    env.update({"GITHUB_EVENT_NAME": "pull_request"})
    env.pop("GITHUB_EVENT_PATH", None)

    result = subprocess.run(
        [sys.executable, str(script), "--use-sample-pr-body"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "Warning:" not in result.stderr


def test_wrapper_uses_sample_body_without_warnings() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    env = os.environ.copy()
    env.update({"GITHUB_EVENT_NAME": "pull_request"})
    env.pop("GITHUB_EVENT_PATH", None)

    result = subprocess.run(
        [sys.executable, str(script), "--use-sample-pr-body"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr.strip() == ""


def test_wrapper_overrides_non_pr_event(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    event_path = tmp_path / "event.json"
    event_path.write_text("{}", encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "GITHUB_EVENT_PATH": str(event_path),
            "GITHUB_EVENT_NAME": "workflow_dispatch",
        }
    )

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
