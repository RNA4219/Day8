from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(_dump_json(payload), encoding="utf-8")


def _iter_capsules(caps_dir: Path) -> Iterable[Path]:
    if not caps_dir.exists():
        return []
    return sorted(caps_dir.glob("*.json"))


def _invoke(*args: str) -> None:
    subprocess.run(
        [
            "python",
            "workflow-cookbook/tools/codemap/update.py",
            *args,
        ],
        check=True,
    )


def _prepare_fixture(root: Path) -> None:
    index_path = root / "index.json"
    index_payload = _load_json(index_path)
    index_payload["generated_at"] = "2000-01-01T00:00:00Z"
    edges = index_payload.get("edges", [])
    if isinstance(edges, list):
        index_payload["edges"] = list(reversed(edges)) + list(edges)
    _write_json(index_path, index_payload)

    caps_dir = root / "caps"
    for cap_path in _iter_capsules(caps_dir):
        cap_payload = _load_json(cap_path)
        cap_payload["deps_out"] = ["stale"]
        cap_payload["deps_in"] = ["stale"]
        cap_payload["generated_at"] = "1999-12-31T23:59:59Z"
        _write_json(cap_path, cap_payload)

    hot_path = root / "hot.json"
    if hot_path.exists():
        hot_payload = _load_json(hot_path)
        hot_payload["generated_at"] = "1999-12-31T23:59:59Z"
        _write_json(hot_path, hot_payload)


def _build_expected(edges: list[object]) -> tuple[list[list[str]], dict[str, list[str]], dict[str, list[str]]]:
    pairs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            continue
        src, dst = (str(edge[0]), str(edge[1]))
        pairs.add((src, dst))
    normalised = [[src, dst] for src, dst in sorted(pairs)]
    deps_out: dict[str, list[str]] = {}
    deps_in: dict[str, list[str]] = {}
    for src, dst in normalised:
        deps_out.setdefault(src, []).append(dst)
        deps_in.setdefault(dst, []).append(src)
    for values in deps_out.values():
        values.sort()
    for values in deps_in.values():
        values.sort()
    return normalised, deps_out, deps_in


def _assert_timestamp_sync(root: Path) -> None:
    index = _load_json(root / "index.json")
    timestamp = index["generated_at"]
    hot_path = root / "hot.json"
    if hot_path.exists():
        assert _load_json(hot_path)["generated_at"] == timestamp
    caps_dir = root / "caps"
    for cap_path in _iter_capsules(caps_dir):
        assert _load_json(cap_path)["generated_at"] == timestamp


def test_update_recomputes_dependencies_for_all_targets(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    day8_target = tmp_path / "docs" / "birdseye"
    cookbook_target = tmp_path / "workflow-cookbook" / "docs" / "birdseye"

    _copy_tree(repo_root / "docs" / "birdseye", day8_target)
    _copy_tree(repo_root / "workflow-cookbook" / "docs" / "birdseye", cookbook_target)

    for target in (day8_target, cookbook_target):
        _prepare_fixture(target)

    targets_arg = f"{day8_target / 'index.json'},{cookbook_target / 'index.json'}"
    _invoke("--targets", targets_arg, "--emit", "index+caps")

    for target in (day8_target, cookbook_target):
        index = _load_json(target / "index.json")
        normalised, deps_out, deps_in = _build_expected(index["edges"])
        assert index["edges"] == normalised
        _assert_timestamp_sync(target)

        caps_dir = target / "caps"
        for cap_path in _iter_capsules(caps_dir):
            capsule = _load_json(cap_path)
            node_id = capsule["id"]
            assert capsule["deps_out"] == deps_out.get(node_id, [])
            assert capsule["deps_in"] == deps_in.get(node_id, [])


def test_emit_modes_and_dry_run_behaviour(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    target = tmp_path / "docs" / "birdseye"
    _copy_tree(repo_root / "docs" / "birdseye", target)
    _prepare_fixture(target)

    index_path = target / "index.json"
    caps_dir = target / "caps"
    cap_path = next(iter(_iter_capsules(caps_dir)))

    index_before = index_path.read_text(encoding="utf-8")
    cap_before = cap_path.read_text(encoding="utf-8")

    _invoke("--targets", str(index_path), "--emit", "index+caps", "--dry-run")
    assert index_path.read_text(encoding="utf-8") == index_before
    assert cap_path.read_text(encoding="utf-8") == cap_before

    _invoke("--targets", str(index_path), "--emit", "caps")
    cap_after_caps = cap_path.read_text(encoding="utf-8")
    assert index_path.read_text(encoding="utf-8") == index_before
    assert cap_after_caps != cap_before

    _invoke("--targets", str(index_path), "--emit", "caps")
    assert cap_path.read_text(encoding="utf-8") == cap_after_caps

    _invoke("--targets", str(index_path), "--emit", "index")
    index_after_index = index_path.read_text(encoding="utf-8")
    assert index_after_index != index_before
    _invoke("--targets", str(index_path), "--emit", "index")
    assert index_path.read_text(encoding="utf-8") == index_after_index

