from __future__ import annotations

import json
from pathlib import Path


def test_birdseye_index_nodes_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    index_path = repo_root / "docs" / "birdseye" / "index.json"

    index_data = json.loads(index_path.read_text(encoding="utf-8"))

    missing_nodes = []
    for node_id in index_data["nodes"].keys():
        node_path = repo_root / node_id
        if not node_path.exists():
            node_path = repo_root.parent / node_id
        if not node_path.exists():
            missing_nodes.append(node_id)

    assert not missing_nodes, (
        "docs/birdseye/index.json に記載されたファイルが存在しません: "
        + ", ".join(sorted(missing_nodes))
    )
