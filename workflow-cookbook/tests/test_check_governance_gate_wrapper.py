"""Integration tests for the repository-level governance gate wrapper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_wrapper_accepts_sample_body_flag() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ci" / "check_governance_gate.py"

    without_flag = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert without_flag.returncode == 1
    assert "PR body data is unavailable" in without_flag.stderr

    with_flag = subprocess.run(
        [sys.executable, str(script), "--use-sample-pr-body"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert with_flag.returncode == 0, with_flag.stderr
