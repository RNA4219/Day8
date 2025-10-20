"""Birdseye インデックスおよびカプセルの再生成ツール。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Mapping


JsonMapping = Mapping[str, object]


class UpdateError(RuntimeError):
    """Raised when Birdseye regeneration fails."""


@dataclass(frozen=True)
class UpdateOptions:
    targets: tuple[Path, ...]
    emit_index: bool
    emit_caps: bool
    dry_run: bool


def _load_json(path: Path) -> JsonMapping:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise UpdateError(f"Birdseye file not found: {path}") from exc
    except OSError as exc:  # pragma: no cover - handled for clarity
        raise UpdateError(f"Failed to read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError(f"Failed to parse JSON {path}: {exc}") from exc


def _dump_json(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _write_json_if_changed(path: Path, payload: object, *, dry_run: bool) -> bool:
    new_text = _dump_json(payload)
    try:
        old_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        old_text = None
    except OSError as exc:  # pragma: no cover - handled for clarity
        raise UpdateError(f"Failed to read {path}: {exc}") from exc

    if old_text == new_text:
        return False

    if dry_run:
        return True

    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError as exc:  # pragma: no cover - handled for clarity
        raise UpdateError(f"Failed to write {path}: {exc}") from exc
    return True


def parse_args(argv: Iterable[str] | None = None) -> UpdateOptions:
    parser = argparse.ArgumentParser(
        description="Regenerate Birdseye index and capsules.",
    )
    parser.add_argument(
        "--targets",
        type=str,
        required=True,
        help="Comma-separated list of Birdseye index.json files to update.",
    )
    parser.add_argument(
        "--emit",
        type=str,
        choices=("index", "caps", "index+caps"),
        default="index+caps",
        help="Select which artefacts to write.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the results without writing files.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    target_paths = tuple(Path(value.strip()) for value in args.targets.split(",") if value.strip())
    if not target_paths:
        parser.error("--targets must contain at least one path")

    emit_index = args.emit in {"index", "index+caps"}
    emit_caps = args.emit in {"caps", "index+caps"}
    return UpdateOptions(
        targets=target_paths,
        emit_index=emit_index,
        emit_caps=emit_caps,
        dry_run=args.dry_run,
    )


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalise_edges(edges: Iterable[object]) -> list[list[str]]:
    pairs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            continue
        source, target = (str(edge[0]), str(edge[1]))
        pairs.add((source, target))
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
    dry_run: bool,
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

        if needs_update or (force_timestamp and capsule.get("generated_at") != timestamp):
            capsule["generated_at"] = timestamp
            _write_json_if_changed(cap_path, capsule, dry_run=dry_run)


def _update_hot_timestamp(hot_path: Path, timestamp: str, *, dry_run: bool) -> None:
    if not hot_path.exists():
        return
    hot_payload = dict(_load_json(hot_path))
    if hot_payload.get("generated_at") == timestamp:
        return
    hot_payload["generated_at"] = timestamp
    _write_json_if_changed(hot_path, hot_payload, dry_run=dry_run)


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


def _update_target(index_path: Path, *, emit_index: bool, emit_caps: bool, dry_run: bool) -> None:
    index_payload = dict(_load_json(index_path))
    current_edges = index_payload.get("edges", [])
    if not isinstance(current_edges, list):
        current_edges = []
    normalised_edges = _normalise_edges(current_edges)

    deps_out, deps_in = _prepare_dependencies(normalised_edges)

    existing_timestamp = str(index_payload.get("generated_at", ""))
    timestamp_for_index = existing_timestamp
    index_payload_for_write = dict(index_payload)

    edges_changed = normalised_edges != list(index_payload.get("edges", []))
    if edges_changed:
        index_payload_for_write["edges"] = normalised_edges

    if emit_index and (edges_changed or index_payload_for_write.get("generated_at") != existing_timestamp):
        timestamp_for_index = _iso_utc_now()
        index_payload_for_write["generated_at"] = timestamp_for_index
        if _write_json_if_changed(index_path, index_payload_for_write, dry_run=dry_run):
            _update_hot_timestamp(index_path.parent / "hot.json", timestamp_for_index, dry_run=dry_run)
    elif emit_index:
        timestamp_for_index = existing_timestamp

    if emit_caps:
        caps_dir = index_path.parent / "caps"
        if caps_dir.exists():
            timestamp_for_caps = timestamp_for_index
            if not emit_index:
                timestamp_for_caps = existing_timestamp
            _update_capsules(
                caps_dir,
                deps_out,
                deps_in,
                timestamp=timestamp_for_caps,
                force_timestamp=emit_index and timestamp_for_caps != existing_timestamp,
                dry_run=dry_run,
            )


def run_update(options: UpdateOptions) -> None:
    for target in options.targets:
        _update_target(target, emit_index=options.emit_index, emit_caps=options.emit_caps, dry_run=options.dry_run)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        run_update(options)
    except UpdateError as exc:
        raise SystemExit(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
