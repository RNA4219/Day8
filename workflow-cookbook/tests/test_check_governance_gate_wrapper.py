"""Integration tests for the repository-level governance gate wrapper."""

from __future__ import annotations

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
