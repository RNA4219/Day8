from __future__ import annotations

import json
import re
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


def _invoke(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python",
            "scripts/birdseye_refresh.py",
            *args,
        ],
        check=True,
        capture_output=capture_output,
        text=True,
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

    _invoke("--docs-dir", str(day8_target), "--docs-dir", str(cookbook_target))

    for target in (day8_target, cookbook_target):
        index = _load_json(target / "index.json")
        normalised, deps_out, deps_in = _build_expected(index["edges"])
        assert index["edges"] == normalised
        _assert_timestamp_sync(target)

        revision = str(index["generated_at"])
        assert re.fullmatch(r"\d{5,}", revision), "generated_at should be a zero-padded serial number"
        for node_meta in index.get("nodes", {}).values():
            assert isinstance(node_meta, dict)
            assert node_meta.get("mtime") == revision

        caps_dir = target / "caps"
        for cap_path in _iter_capsules(caps_dir):
            capsule = _load_json(cap_path)
            node_id = capsule["id"]
            assert capsule["deps_out"] == deps_out.get(node_id, [])
            assert capsule["deps_in"] == deps_in.get(node_id, [])


def test_refresh_dry_run_and_updates(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    target = tmp_path / "docs" / "birdseye"
    _copy_tree(repo_root / "docs" / "birdseye", target)
    _prepare_fixture(target)

    index_path = target / "index.json"
    caps_dir = target / "caps"
    cap_path = next(iter(_iter_capsules(caps_dir)))

    index_before = index_path.read_text(encoding="utf-8")
    cap_before = cap_path.read_text(encoding="utf-8")

    result = _invoke("--docs-dir", str(target), "--dry-run", capture_output=True)
    assert result.stdout
    assert "[dry-run]" in result.stdout
    assert str(index_path) in result.stdout
    assert cap_path.name in result.stdout
    assert index_path.read_text(encoding="utf-8") == index_before
    assert cap_path.read_text(encoding="utf-8") == cap_before

    _invoke("--docs-dir", str(target))
    cap_after_caps = cap_path.read_text(encoding="utf-8")
    assert cap_after_caps != cap_before
    index_after_first = index_path.read_text(encoding="utf-8")
    assert index_after_first != index_before

    _invoke("--docs-dir", str(target))
    assert index_path.read_text(encoding="utf-8") != index_after_first
    assert cap_path.read_text(encoding="utf-8") != cap_after_caps


def test_refresh_syncs_timestamps_for_normalised_edges(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    target = tmp_path / "docs" / "birdseye"
    _copy_tree(repo_root / "docs" / "birdseye", target)

    index_path = target / "index.json"
    index_payload = _load_json(index_path)
    normalised, _, _ = _build_expected(list(index_payload.get("edges", [])))
    original_timestamp = "2000-01-01T00:00:00Z"
    index_payload["edges"] = normalised
    index_payload["generated_at"] = original_timestamp
    _write_json(index_path, index_payload)

    hot_path = target / "hot.json"
    if hot_path.exists():
        hot_payload = _load_json(hot_path)
        hot_payload["generated_at"] = original_timestamp
        _write_json(hot_path, hot_payload)

    caps_dir = target / "caps"
    cap_path = next(iter(_iter_capsules(caps_dir)), None)
    original_cap_timestamp = None
    if cap_path is not None:
        cap_payload = _load_json(cap_path)
        original_cap_timestamp = cap_payload.get("generated_at")

    dry_run = _invoke(
        "--docs-dir",
        str(target),
        "--dry-run",
        capture_output=True,
    )
    assert dry_run.stdout
    assert "[dry-run]" in dry_run.stdout
    assert str(index_path) in dry_run.stdout
    assert _load_json(index_path)["generated_at"] == original_timestamp
    if hot_path.exists():
        assert "hot.json" in dry_run.stdout
        assert _load_json(hot_path)["generated_at"] == original_timestamp
    if cap_path is not None:
        assert _load_json(cap_path)["generated_at"] == original_cap_timestamp

    _invoke("--docs-dir", str(target))
    updated_index = _load_json(index_path)
    first_timestamp = str(updated_index["generated_at"])
    assert first_timestamp != original_timestamp
    if hot_path.exists():
        assert _load_json(hot_path)["generated_at"] == first_timestamp
    if cap_path is not None:
        assert _load_json(cap_path)["generated_at"] == first_timestamp

    _invoke("--docs-dir", str(target))
    second_index = _load_json(index_path)
    second_timestamp = str(second_index["generated_at"])
    assert second_timestamp != first_timestamp
    if hot_path.exists():
        assert _load_json(hot_path)["generated_at"] == second_timestamp
    if cap_path is not None:
        assert _load_json(cap_path)["generated_at"] == second_timestamp

    _invoke("--docs-dir", str(target))
    final_index = _load_json(index_path)
    final_timestamp = str(final_index["generated_at"])
    assert final_timestamp != second_timestamp
    _assert_timestamp_sync(target)


def test_refresh_syncs_hot_timestamp_when_present(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    target = tmp_path / "docs" / "birdseye"
    _copy_tree(repo_root / "docs" / "birdseye", target)

    index_path = target / "index.json"
    index_payload = _load_json(index_path)
    index_payload["generated_at"] = "2000-01-01T00:00:00Z"
    _write_json(index_path, index_payload)

    hot_path = target / "hot.json"
    if hot_path.exists():
        hot_payload = _load_json(hot_path)
        hot_payload["generated_at"] = "1999-12-31T23:59:59Z"
        _write_json(hot_path, hot_payload)

    _invoke("--docs-dir", str(target))

    if hot_path.exists():
        hot_payload = _load_json(hot_path)
        assert hot_payload["generated_at"] == _load_json(index_path)["generated_at"]
