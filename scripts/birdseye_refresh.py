from __future__ import annotations
import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
DEFAULT_DOCS_DIRS: tuple[Path, ...] = (
    Path("docs/birdseye"),
    Path("workflow-cookbook/docs/birdseye"),
)

class RefreshError(RuntimeError):
    """Raised when the Birdseye refresh flow fails."""

@dataclass(frozen=True)
class RefreshOptions:
    docs_dirs: tuple[Path, ...]
    dry_run: bool

def _load_codemap_update_module():
    target_path = Path(__file__).resolve().parent.parent / "workflow-cookbook" / "tools" / "codemap" / "update.py"
    spec = importlib.util.spec_from_file_location("codemap_update", target_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RefreshError(f"Failed to load codemap update module: {target_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def _parse_docs_dirs(raw_values: Sequence[str]) -> tuple[Path, ...]:
    if not raw_values:
        return DEFAULT_DOCS_DIRS

    collected: list[Path] = []
    for raw in raw_values:
        for candidate in raw.split(","):
            text = candidate.strip()
            if text:
                collected.append(Path(text))
    if not collected:
        return DEFAULT_DOCS_DIRS
    return tuple(collected)

def parse_args(argv: Iterable[str] | None = None) -> RefreshOptions:
    parser = argparse.ArgumentParser(description="Refresh Birdseye artefacts for Day8.")
    parser.add_argument(
        "--docs-dir",
        action="append",
        default=[],
        help="Directory containing a Birdseye index.json (repeatable, comma separated).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the results without writing files.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    docs_dirs = _parse_docs_dirs(args.docs_dir)
    return RefreshOptions(docs_dirs=docs_dirs, dry_run=args.dry_run)

def _resolve_index_paths(docs_dirs: Iterable[Path]) -> tuple[Path, ...]:
    index_paths: list[Path] = []
    for docs_dir in docs_dirs:
        index_path = docs_dir / "index.json"
        if not index_path.exists():
            raise RefreshError(f"Birdseye index.json not found: {index_path}")
        index_paths.append(index_path)
    if not index_paths:
        raise RefreshError("No Birdseye index.json files resolved.")
    return tuple(index_paths)

def run_refresh(options: RefreshOptions) -> None:
    index_paths = _resolve_index_paths(options.docs_dirs)
    codemap_update = _load_codemap_update_module()
    update_options = codemap_update.UpdateOptions(
        targets=index_paths,
        emit_index=True,
        emit_caps=True,
        dry_run=options.dry_run,
    )
    codemap_update.run_update(update_options)

def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        run_refresh(options)
    except RefreshError as exc:
        raise SystemExit(str(exc))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
