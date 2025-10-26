from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_pack_module() -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("workflow_context_pack", root / "tools" / "context" / "pack.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load context pack module")
    if "ppr" not in sys.modules:
        stub = ModuleType("ppr")
        def _personalize_scores(*args, **kwargs):
            return {}

        stub.personalize_scores = _personalize_scores  # type: ignore[attr-defined]
        sys.modules["ppr"] = stub
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_base_signals_role_scores() -> None:
    pack = _load_pack_module()
    cfg = pack._load_config(Path(__file__).resolve().parents[1] / "tools" / "context" / "config.yaml")
    profile = {"keywords": set(), "role": "impl"}

    node_common = {
        "path": "docs/runbook.md",
        "heading": "Runbook",
        "mtime": "",
    }

    matching = {"id": "node-1", "role": "impl", **node_common}
    mismatch = {"id": "node-2", "role": "ops", **node_common}
    missing = {"id": "node-3", **node_common}

    match_signals = pack._base_signals(matching, profile, set(), {"node-1": 0.0}, cfg)
    mismatch_signals = pack._base_signals(mismatch, profile, set(), {"node-2": 0.0}, cfg)
    missing_signals = pack._base_signals(missing, profile, set(), {"node-3": 0.0}, cfg)

    assert match_signals["role"] == 0.6
    assert mismatch_signals["role"] == 0.2
    assert missing_signals["role"] == 0.4


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
