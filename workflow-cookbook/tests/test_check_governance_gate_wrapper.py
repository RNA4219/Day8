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
