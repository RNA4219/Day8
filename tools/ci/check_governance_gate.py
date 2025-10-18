from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    legacy_script = repo_root / "workflow-cookbook" / "tools" / "ci" / "check_governance_gate.py"
    if not legacy_script.is_file():
        raise FileNotFoundError(legacy_script)
    runpy.run_path(str(legacy_script), run_name="__main__")


if __name__ == "__main__":
    main()
