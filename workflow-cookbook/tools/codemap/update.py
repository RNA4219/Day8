"""Birdseye 再生成ツール。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Mapping


JsonMapping = Mapping[str, object]


@dataclass(frozen=True)
class UpdateOptions:
    targets: tuple[Path, ...]
    emit_index: bool
    emit_caps: bool


def _load_json(path: Path) -> JsonMapping:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _dump_json(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _write_json_if_changed(path: Path, payload: object) -> bool:
    new_text = _dump_json(payload)
    try:
        old_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        old_text = None
    if old_text == new_text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def parse_args(argv: Iterable[str] | None = None) -> UpdateOptions:
    parser = argparse.ArgumentParser(
        description="Regenerate Birdseye index and capsules.",
    )
    parser.add_argument(
        "--targets",
        type=str,
        required=True,
        help="Comma-separated list of Birdseye resources to analyse.",
    )
    parser.add_argument(
        "--emit",
        type=str,
        choices=("index", "caps", "index+caps"),
        default="index+caps",
        help="Select which artefacts to write.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    target_paths = tuple(Path(value.strip()) for value in args.targets.split(",") if value.strip())
    if not target_paths:
        parser.error("--targets must contain at least one path")

    emit_index = args.emit in {"index", "index+caps"}
    emit_caps = args.emit in {"caps", "index+caps"}
    return UpdateOptions(targets=target_paths, emit_index=emit_index, emit_caps=emit_caps)


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalise_edges(edges: Iterable[Iterable[str]]) -> list[list[str]]:
    pairs = {(edge[0], edge[1]) for edge in edges if len(edge) == 2}
    return [[src, dst] for src, dst in sorted(pairs)]


def _iter_caps(caps_dir: Path) -> Iterator[Path]:
    yield from sorted(caps_dir.glob("*.json"))


def _update_capsules(
    caps_dir: Path,
    deps_out: Mapping[str, list[str]],
    deps_in: Mapping[str, list[str]],
    *,
    timestamp: str,
    force_timestamp: bool,
) -> None:
    for cap_path in _iter_caps(caps_dir):
        capsule = dict(_load_json(cap_path))
        node_id = str(capsule.get("id", ""))
        new_out = deps_out.get(node_id, [])
        new_in = deps_in.get(node_id, [])

        needs_update = False
        if list(capsule.get("deps_out", [])) != new_out:
            capsule["deps_out"] = new_out
            needs_update = True
        if list(capsule.get("deps_in", [])) != new_in:
            capsule["deps_in"] = new_in
            needs_update = True
        if force_timestamp and capsule.get("generated_at") != timestamp:
            capsule["generated_at"] = timestamp
            needs_update = True
        elif needs_update:
            capsule["generated_at"] = timestamp
        if needs_update:
            _write_json_if_changed(cap_path, capsule)


def _update_hot_timestamp(hot_path: Path, timestamp: str) -> None:
    if not hot_path.exists():
        return
    hot_payload = dict(_load_json(hot_path))
    if hot_payload.get("generated_at") != timestamp:
        hot_payload["generated_at"] = timestamp
        _write_json_if_changed(hot_path, hot_payload)


def _update_target(index_path: Path, *, emit_index: bool, emit_caps: bool) -> None:
    index_payload = dict(_load_json(index_path))
    current_edges = index_payload.get("edges", [])
    normalised_edges = _normalise_edges(current_edges)

    index_requires_write = emit_index and normalised_edges != current_edges

    deps_out: dict[str, list[str]] = {}
    deps_in: dict[str, list[str]] = {}
    for source, target in normalised_edges:
        deps_out.setdefault(source, []).append(target)
        deps_in.setdefault(target, []).append(source)

    for values in deps_out.values():
        values.sort()
    for values in deps_in.values():
        values.sort()

    timestamp = _iso_utc_now() if index_requires_write else str(index_payload.get("generated_at", ""))

    if index_requires_write:
        index_payload["edges"] = normalised_edges
        index_payload["generated_at"] = timestamp
        _write_json_if_changed(index_path, index_payload)
        _update_hot_timestamp(index_path.parent / "hot.json", timestamp)

    if emit_caps:
        caps_dir = index_path.parent / "caps"
        if caps_dir.exists():
            caps_timestamp = timestamp if index_requires_write else str(index_payload.get("generated_at", ""))
            _update_capsules(
                caps_dir,
                deps_out,
                deps_in,
                timestamp=caps_timestamp,
                force_timestamp=index_requires_write,
            )


def run_update(options: UpdateOptions) -> None:
    for target in options.targets:
        _update_target(target, emit_index=options.emit_index, emit_caps=options.emit_caps)


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    run_update(options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
