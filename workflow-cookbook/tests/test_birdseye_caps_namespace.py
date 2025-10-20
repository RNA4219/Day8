"""Birdseye caps namespaceの整合性を検証するテスト。"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "docs" / "birdseye" / "index.json"
DOCS_INDEX_PATH = REPO_ROOT / "docs" / "birdseye" / "index.json"

PRIORITIZATION_NODE = "workflow-cookbook/governance/prioritization.yaml"
PRIORITIZATION_CAPS = REPO_ROOT / "docs" / "birdseye" / "caps" / (
    "workflow-cookbook.governance.prioritization.yaml.json"
)
PRIORITIZATION_EXPECTED_INCOMING = [
    "workflow-cookbook/EVALUATION.md",
    "workflow-cookbook/HUB.codex.md",
    "workflow-cookbook/README.md",
    "workflow-cookbook/TASK.codex.md",
]
PRIORITIZATION_EXPECTED_OUTGOING = [
    "workflow-cookbook/EVALUATION.md",
    "workflow-cookbook/README.md",
    "workflow-cookbook/TASK.codex.md",
]


@pytest.fixture(scope="module")
def birdseye_index() -> dict:
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def node_caps_paths(birdseye_index: dict) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for node, meta in birdseye_index["nodes"].items():
        mapping[node] = REPO_ROOT / Path(meta["caps"])
    return mapping


@pytest.fixture(scope="module")
def index_nodes(birdseye_index: dict) -> set[str]:
    nodes: set[str] = set()
    for edge in birdseye_index["edges"]:
        assert len(edge) == 2, "edge must contain exactly two nodes"
        src, dst = edge
        nodes.add(src)
        nodes.add(dst)
    return nodes


@pytest.fixture(scope="module")
def adjacency(birdseye_index: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for src, dst in birdseye_index["edges"]:
        outgoing[src].append(dst)
        incoming[dst].append(src)
    for mapping in (outgoing, incoming):
        for node in mapping:
            mapping[node].sort()
    return outgoing, incoming


def test_caps_file_exists_and_matches_id(
    index_nodes: set[str], node_caps_paths: dict[str, Path]
) -> None:
    for node in sorted(index_nodes):
        assert node in node_caps_paths, f"node metadata missing for {node}"
        caps_path = node_caps_paths[node]
        assert caps_path.exists(), f"caps file missing for node {node}"
        with caps_path.open("r", encoding="utf-8") as f:
            caps_data = json.load(f)
        assert caps_data["id"] == node


def test_caps_dependencies_match_index(
    index_nodes: set[str],
    adjacency: tuple[dict[str, list[str]], dict[str, list[str]]],
    node_caps_paths: dict[str, Path],
) -> None:
    outgoing, incoming = adjacency
    for node in sorted(index_nodes):
        assert node in node_caps_paths, f"node metadata missing for {node}"
        caps_path = node_caps_paths[node]
        assert caps_path.exists(), f"caps file missing for node {node}"
        with caps_path.open("r", encoding="utf-8") as f:
            caps_data = json.load(f)
        deps_out = sorted(caps_data.get("deps_out", []))
        deps_in = sorted(caps_data.get("deps_in", []))
        assert deps_out == outgoing.get(node, []), f"deps_out mismatch for {node}"
        assert deps_in == incoming.get(node, []), f"deps_in mismatch for {node}"


def _load_docs_birdseye_index() -> dict:
    with DOCS_INDEX_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_adjacency(index: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for src, dst in index["edges"]:
        outgoing[src].append(dst)
        incoming[dst].append(src)
    for mapping in (outgoing, incoming):
        for key in mapping:
            mapping[key].sort()
    return outgoing, incoming


def test_prioritization_node_registered() -> None:
    index = _load_docs_birdseye_index()
    assert PRIORITIZATION_NODE in index["nodes"], (
        "prioritization node missing from docs/birdseye index"
    )
    meta = index["nodes"][PRIORITIZATION_NODE]
    caps_path = REPO_ROOT / Path(meta["caps"])
    assert caps_path == PRIORITIZATION_CAPS
    assert caps_path.exists()
    with caps_path.open("r", encoding="utf-8") as handle:
        caps_data = json.load(handle)
    assert caps_data["id"] == PRIORITIZATION_NODE


def test_prioritization_edges() -> None:
    index = _load_docs_birdseye_index()
    outgoing, incoming = _build_adjacency(index)
    assert incoming.get(PRIORITIZATION_NODE, []) == PRIORITIZATION_EXPECTED_INCOMING
    assert outgoing.get(PRIORITIZATION_NODE, []) == PRIORITIZATION_EXPECTED_OUTGOING
    with PRIORITIZATION_CAPS.open("r", encoding="utf-8") as handle:
        caps_data = json.load(handle)
    assert sorted(caps_data.get("deps_in", [])) == PRIORITIZATION_EXPECTED_INCOMING
    assert sorted(caps_data.get("deps_out", [])) == PRIORITIZATION_EXPECTED_OUTGOING
