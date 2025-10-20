from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _setup_birdseye(
    root: Path,
    *,
    timestamp: str,
    edges: list[list[str]],
    caps: dict[str, tuple[list[str], list[str]]],
    hot_entries: list[dict[str, Any]],
) -> None:
    caps_dir = root / "caps"
    caps_dir.mkdir(parents=True)

    nodes = {}
    for node_id, (deps_out, deps_in) in caps.items():
        nodes[node_id] = {"role": "doc", "caps": f"caps/{node_id}.json", "mtime": timestamp}
        _write_json(
            caps_dir / f"{node_id}.json",
            {
                "id": node_id,
                "role": "doc",
                "deps_out": deps_out,
                "deps_in": deps_in,
                "generated_at": timestamp,
            },
        )

    _write_json(root / "index.json", {"generated_at": timestamp, "nodes": nodes, "edges": edges})
    _write_json(root / "hot.json", {"generated_at": timestamp, "entries": hot_entries})


def _invoke_cli(base: Path, emit: str) -> None:
    subprocess.run(
        [
            "python",
            "workflow-cookbook/tools/codemap/update.py",
            "--targets",
            str(base / "index.json"),
            "--emit",
            emit,
        ],
        check=True,
    )


def test_updates_generated_at_and_dependencies(tmp_path: Path) -> None:
    timestamp = "2024-01-01T00:00:00Z"
    birdseye_dir = tmp_path / "birdseye"
    _setup_birdseye(
        birdseye_dir,
        timestamp=timestamp,
        edges=[
            ["beta.md", "alpha.md"],
            ["alpha.md", "beta.md"],
            ["alpha.md", "beta.md"],
        ],
        caps={
            "alpha.md": ([], ["beta.md", "beta.md"]),
            "beta.md": ([], []),
        },
        hot_entries=[{"id": "alpha.md", "caps": "caps/alpha.md.json", "reason": "critical"}],
    )

    _invoke_cli(birdseye_dir, "index+caps")

    index_path = birdseye_dir / "index.json"
    caps_dir = birdseye_dir / "caps"
    hot_path = birdseye_dir / "hot.json"

    index_after = json.loads(index_path.read_text(encoding="utf-8"))
    alpha_after = json.loads((caps_dir / "alpha.md.json").read_text(encoding="utf-8"))
    beta_after = json.loads((caps_dir / "beta.md.json").read_text(encoding="utf-8"))

    assert index_after["generated_at"] != timestamp
    assert index_after["edges"] == [["alpha.md", "beta.md"], ["beta.md", "alpha.md"]]
    assert alpha_after["deps_out"] == ["beta.md"]
    assert alpha_after["deps_in"] == ["beta.md"]
    assert beta_after["deps_out"] == ["alpha.md"]
    assert beta_after["deps_in"] == ["alpha.md"]
    assert alpha_after["generated_at"] == index_after["generated_at"]
    assert beta_after["generated_at"] == index_after["generated_at"]
    assert json.loads(hot_path.read_text(encoding="utf-8"))["generated_at"] == index_after["generated_at"]


def test_emit_flags_and_idempotence(tmp_path: Path) -> None:
    timestamp = "2024-05-01T00:00:00Z"
    birdseye_dir = tmp_path / "birdseye"
    _setup_birdseye(
        birdseye_dir,
        timestamp=timestamp,
        edges=[["gamma.md", "gamma.md"]],
        caps={"gamma.md": ([], ["orphan"])},
        hot_entries=[],
    )

    index_path = birdseye_dir / "index.json"
    caps_path = birdseye_dir / "caps/gamma.md.json"
    hot_path = birdseye_dir / "hot.json"
    expected_index = index_path.read_text(encoding="utf-8")

    _invoke_cli(birdseye_dir, "caps")
    caps_after = json.loads(caps_path.read_text(encoding="utf-8"))
    assert index_path.read_text(encoding="utf-8") == expected_index
    assert caps_after["deps_in"] == ["gamma.md"]
    assert caps_after["generated_at"] == timestamp

    _invoke_cli(birdseye_dir, "index")
    index_once = index_path.read_text(encoding="utf-8")
    hot_once = hot_path.read_text(encoding="utf-8")
    _invoke_cli(birdseye_dir, "index")
    assert index_path.read_text(encoding="utf-8") == index_once
    assert hot_path.read_text(encoding="utf-8") == hot_once
