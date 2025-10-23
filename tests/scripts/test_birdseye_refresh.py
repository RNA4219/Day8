from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _copy_docs_tree(project_root: Path, workspace: Path, relative: Path) -> Path:
    source = project_root / relative
    destination = workspace / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return destination


def _normalise_edges(edges: Iterable[object]) -> list[list[str]]:
    pairs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            continue
        pairs.add((str(edge[0]), str(edge[1])))
    return [[src, dst] for src, dst in sorted(pairs)]


def _prepare_dependencies(edges: list[list[str]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    deps_out: dict[str, list[str]] = {}
    deps_in: dict[str, list[str]] = {}
    for source, target in edges:
        deps_out.setdefault(source, []).append(target)
        deps_in.setdefault(target, []).append(source)
    for values in deps_out.values():
        values.sort()
    for values in deps_in.values():
        values.sort()
    return deps_out, deps_in


def _mutate_payloads(
    index_path: Path, hot_path: Path | None, capsule_path: Path, *, generated_at: str
) -> None:
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["generated_at"] = generated_at
    nodes = index_payload.get("nodes")
    if isinstance(nodes, dict):
        for node_meta in nodes.values():
            if isinstance(node_meta, dict):
                node_meta["mtime"] = generated_at
    index_path.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if hot_path is not None and hot_path.exists():
        hot_payload = json.loads(hot_path.read_text(encoding="utf-8"))
        hot_payload["generated_at"] = generated_at
        hot_path.write_text(
            json.dumps(hot_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    capsule_payload = json.loads(capsule_path.read_text(encoding="utf-8"))
    capsule_payload["deps_out"] = ["stale-out"]
    capsule_payload["deps_in"] = ["stale-in"]
    capsule_payload["generated_at"] = generated_at
    capsule_path.write_text(
        json.dumps(capsule_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_birdseye_refresh_cli(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parent.parent.parent
    workspace = tmp_path / "workspace"
    docs_dir = _copy_docs_tree(project_root, workspace, Path("docs") / "birdseye")
    cookbook_dir = _copy_docs_tree(
        project_root, workspace, Path("workflow-cookbook") / "docs" / "birdseye"
    )

    docs_index = docs_dir / "index.json"
    docs_hot = docs_dir / "hot.json"
    docs_capsule = docs_dir / "caps" / "README.md.json"
    cookbook_index = cookbook_dir / "index.json"
    cookbook_hot = cookbook_dir / "hot.json"
    cookbook_capsule = cookbook_dir / "caps" / "GUARDRAILS.md.json"

    _mutate_payloads(docs_index, docs_hot, docs_capsule, generated_at="00000")
    _mutate_payloads(cookbook_index, cookbook_hot, cookbook_capsule, generated_at="00000")

    before_paths = [
        docs_index,
        docs_capsule,
        cookbook_index,
        cookbook_capsule,
    ]
    if docs_hot.exists():
        before_paths.append(docs_hot)
    if cookbook_hot.exists():
        before_paths.append(cookbook_hot)
    before_texts = {path: path.read_text(encoding="utf-8") for path in before_paths}

    command = [
        sys.executable,
        "scripts/birdseye_refresh.py",
        "--docs-dir",
        str(docs_dir),
        "--docs-dir",
        str(cookbook_dir),
        "--dry-run",
    ]
    subprocess.run(command, cwd=project_root, check=True, capture_output=True, text=True)

    for path, before in before_texts.items():
        assert path.read_text(encoding="utf-8") == before

    monkeypatch.chdir(project_root)
    run_command = [
        sys.executable,
        "scripts/birdseye_refresh.py",
        "--docs-dir",
        str(docs_dir),
        "--docs-dir",
        str(cookbook_dir),
    ]
    subprocess.run(run_command, check=True)

    docs_payload = json.loads(docs_index.read_text(encoding="utf-8"))
    docs_revision = docs_payload["generated_at"]
    assert docs_revision == "00001"
    docs_nodes = docs_payload.get("nodes", {})
    assert isinstance(docs_nodes, dict)
    assert docs_nodes["README.md"]["mtime"] == docs_revision

    docs_edges = _normalise_edges(docs_payload.get("edges", []))
    docs_deps_out, docs_deps_in = _prepare_dependencies(docs_edges)
    docs_caps_payload = json.loads(docs_capsule.read_text(encoding="utf-8"))
    assert docs_caps_payload["generated_at"] == docs_revision
    assert docs_caps_payload["deps_out"] == docs_deps_out.get("README.md", [])
    assert docs_caps_payload["deps_in"] == docs_deps_in.get("README.md", [])

    if docs_hot.exists():
        docs_hot_payload = json.loads(docs_hot.read_text(encoding="utf-8"))
        assert docs_hot_payload["generated_at"] == docs_revision

    cookbook_payload = json.loads(cookbook_index.read_text(encoding="utf-8"))
    cookbook_revision = cookbook_payload["generated_at"]
    assert cookbook_revision == "00001"
    cookbook_nodes = cookbook_payload.get("nodes", {})
    assert isinstance(cookbook_nodes, dict)
    assert cookbook_nodes["workflow-cookbook/GUARDRAILS.md"]["mtime"] == cookbook_revision

    cookbook_edges = _normalise_edges(cookbook_payload.get("edges", []))
    cookbook_deps_out, cookbook_deps_in = _prepare_dependencies(cookbook_edges)
    cookbook_caps_payload = json.loads(cookbook_capsule.read_text(encoding="utf-8"))
    assert cookbook_caps_payload["generated_at"] == cookbook_revision
    assert cookbook_caps_payload["deps_out"] == cookbook_deps_out.get(
        "workflow-cookbook/GUARDRAILS.md", []
    )
    assert cookbook_caps_payload["deps_in"] == cookbook_deps_in.get(
        "workflow-cookbook/GUARDRAILS.md", []
    )

    if cookbook_hot.exists():
        cookbook_hot_payload = json.loads(cookbook_hot.read_text(encoding="utf-8"))
        assert cookbook_hot_payload["generated_at"] == cookbook_revision
