"""Birdseye caps の codemap tooling コマンドを検証するテスト。"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPS_DIR = REPO_ROOT / "docs" / "birdseye" / "caps"
EXPECTED_TARGET = "docs/birdseye/index.json"


@pytest.mark.parametrize("caps_path", sorted(CAPS_DIR.glob("*.json")))
def test_codemap_tooling_targets_index_json(caps_path: Path) -> None:
    with caps_path.open("r", encoding="utf-8") as f:
        caps_data = json.load(f)

    maintenance = caps_data.get("maintenance", {})
    tooling_commands = maintenance.get("tooling", [])
    codemap_commands = [
        command
        for command in tooling_commands
        if "workflow-cookbook/tools/codemap/update.py" in command
    ]

    for command in codemap_commands:
        args = shlex.split(command)
        try:
            targets_index = args.index("--targets")
        except ValueError:
            pytest.fail(
                f"--targets が見つかりません: {caps_path} のコマンド {command!r}",
            )

        if targets_index + 1 >= len(args):
            pytest.fail(
                f"--targets の引数が不足しています: {caps_path} のコマンド {command!r}",
            )

        target_arg = args[targets_index + 1]
        targets = target_arg.split(",")
        assert EXPECTED_TARGET in targets, (
            f"{caps_path} の codemap コマンド {command!r} が index.json を指していません"
        )
