from __future__ import annotations

import json
from pathlib import Path


def test_birdseye_index_nodes_are_files() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "workflow-cookbook" / "docs" / "birdseye" / "index.json"
    index_data = json.loads(index_path.read_text(encoding="utf-8"))

    missing_nodes: list[str] = []
    for node_id in index_data["nodes"].keys():
        node_path = repo_root / node_id
        if not node_path.is_file():
            missing_nodes.append(node_id)

    assert not missing_nodes, f"Missing files for node targets: {missing_nodes}"
