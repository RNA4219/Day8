from __future__ import annotations

import json
from pathlib import Path


def test_birdseye_index_nodes_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
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


def test_birdseye_registers_docs_birdseye_md() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "docs" / "birdseye" / "index.json"
    hot_path = repo_root / "docs" / "birdseye" / "hot.json"

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    birdseye_node = index_data["nodes"].get("docs/BIRDSEYE.md")

    assert birdseye_node is not None, "docs/BIRDSEYE.md が nodes に存在しません"
    assert (
        birdseye_node.get("caps") == "docs/birdseye/caps/docs.BIRDSEYE.md.json"
    ), "docs/BIRDSEYE.md ノードの caps が想定と異なります"
    assert [
        "docs/ROADMAP_AND_SPECS.md",
        "docs/BIRDSEYE.md",
    ] in index_data["edges"], "docs/BIRDSEYE.md へのエッジが不足しています"

    hot_data = json.loads(hot_path.read_text(encoding="utf-8"))
    hot_ids = {entry["id"] for entry in hot_data["entries"]}
    assert "docs/BIRDSEYE.md" in hot_ids, "docs/BIRDSEYE.md がホットリストに登録されていません"


def test_birdseye_generated_at_matches_hot_json() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    index_path = repo_root / "docs" / "birdseye" / "index.json"
    hot_path = repo_root / "docs" / "birdseye" / "hot.json"

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    hot_data = json.loads(hot_path.read_text(encoding="utf-8"))

    assert (
        index_data["generated_at"] == hot_data["generated_at"]
    ), "docs/birdseye/index.json と docs/birdseye/hot.json の generated_at が一致しません"
