from __future__ import annotations

import json
from pathlib import Path


def test_birdseye_includes_task_seed_nodes() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "docs" / "birdseye" / "index.json"
    hot_path = repo_root / "docs" / "birdseye" / "hot.json"

    index_data = json.loads(index_path.read_text(encoding="utf-8"))

    nodes = index_data["nodes"]
    assert "docs/TASKS.md" in nodes
    assert "docs/seeds/README.md" in nodes

    edges = [tuple(edge) for edge in index_data["edges"]]
    assert ("docs/README.md", "docs/TASKS.md") in edges
    assert ("docs/TASKS.md", "docs/seeds/README.md") in edges

    for node_id in ("docs/TASKS.md", "docs/seeds/README.md"):
        caps_path = repo_root / nodes[node_id]["caps"]
        assert caps_path.is_file(), f"Missing capsule for {node_id}: {caps_path}"

    hot_data = json.loads(hot_path.read_text(encoding="utf-8"))
    hot_ids = {entry["id"] for entry in hot_data["entries"]}
    assert "docs/TASKS.md" in hot_ids
