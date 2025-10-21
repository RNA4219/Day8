"""Birdseye caps の codemap tooling コマンドを検証するテスト。"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPS_DIR = REPO_ROOT / "docs" / "birdseye" / "caps"
EXPECTED_DOCS_DIRS = (
    "docs/birdseye",
    "workflow-cookbook/docs/birdseye",
)


@pytest.mark.parametrize("caps_path", sorted(CAPS_DIR.glob("*.json")))
def test_codemap_tooling_targets_index_json(caps_path: Path) -> None:
    with caps_path.open("r", encoding="utf-8") as f:
        caps_data = json.load(f)

    maintenance = caps_data.get("maintenance", {})
    tooling_commands = maintenance.get("tooling", [])
    refresh_commands = [
        command
        for command in tooling_commands
        if "scripts/birdseye_refresh.py" in command
    ]

    for command in refresh_commands:
        args = shlex.split(command)
        docs_dir_args = [
            args[index + 1]
            for index, token in enumerate(args)
            if token == "--docs-dir" and index + 1 < len(args)
        ]

        missing = [
            expected
            for expected in EXPECTED_DOCS_DIRS
            if expected not in docs_dir_args
        ]
        assert not missing, (
            f"{caps_path} の Birdseye refresh コマンド {command!r} に "
            f"必要な --docs-dir が不足しています: {missing}"
        )
