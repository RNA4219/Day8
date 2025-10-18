"""Tests for the birdseye index nodes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


def _load_index() -> Tuple[Dict[str, Any], Path]:
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "workflow-cookbook" / "docs" / "birdseye" / "index.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return data, repo_root


def test_birdseye_nodes_exist() -> None:
    data, repo_root = _load_index()

    missing = [
        node_id
        for node_id in data["nodes"].keys()
        if not (repo_root / node_id).exists()
    ]

    assert not missing, (
        "Missing files referenced in birdseye index: " + ", ".join(missing)
    )
