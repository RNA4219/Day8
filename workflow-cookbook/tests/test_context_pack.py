from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_pack_generates_ppr_scores(tmp_path: Path) -> None:
    graph = {
        "nodes": [
            {
                "id": "docs/runbook.md#h1-build",
                "path": "docs/runbook.md",
                "heading": "Build Feature",
                "depth": 1,
                "mtime": "2025-01-01T00:00:00Z",
                "tok": 120,
                "role": "impl",
            },
            {
                "id": "docs/runbook.md#h2-ops",
                "path": "docs/runbook.md",
                "heading": "Operations Guide",
                "depth": 2,
                "mtime": "2024-05-01T00:00:00Z",
                "tok": 140,
                "role": "ops",
            },
            {
                "id": "docs/spec.md#h2-overview",
                "path": "docs/spec.md",
                "heading": "System Overview",
                "depth": 2,
                "mtime": "2023-01-01T00:00:00Z",
                "tok": 160,
                "role": "spec",
            },
        ],
        "edges": [
            {"src": "docs/runbook.md#h1-build", "dst": "docs/runbook.md#h2-ops", "type": "link"},
            {"src": "docs/runbook.md#h2-ops", "dst": "docs/spec.md#h2-overview", "type": "link"},
            {"src": "docs/spec.md#h2-overview", "dst": "docs/runbook.md#h1-build", "type": "link"},
        ],
        "meta": {"generated_at": "2025-01-02T00:00:00Z", "version": "1"},
    }
    graph_path = tmp_path / "graph.json"
    _write_json(graph_path, graph)

    root = Path(__file__).resolve().parents[1]
    pack_script = root / "tools" / "context" / "pack.py"
    output_path = tmp_path / "pack.json"

    subprocess.run(
        [
            sys.executable,
            str(pack_script),
            "--graph",
            str(graph_path),
            "--output",
            str(output_path),
            "--intent",
            "INT-4242 implement build pipeline",
            "--budget",
            "400",
            "--ppr",
            "--diff",
            "docs/runbook.md",
        ],
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["intent"] == "INT-4242 implement build pipeline"
    assert payload["budget"] == "400"
    assert payload["sections"], "sections should not be empty"
    first = payload["sections"][0]
    assert "ppr" in first["why"], "why block should include ppr score"
    assert payload["metrics"]["token_in"] <= 400
    assert payload["metrics"]["token_in"] > 0
