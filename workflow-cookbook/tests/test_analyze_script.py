from __future__ import annotations

from pathlib import Path
import py_compile


def test_analyze_script_compiles(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "analyze.py"
    cfile = tmp_path / "analyze.pyc"

    compiled_path = py_compile.compile(
        script_path,
        cfile=cfile,
        doraise=True,
    )

    assert Path(compiled_path) == cfile
import py_compile
from pathlib import Path


def test_analyze_script_compiles() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "analyze.py"
    py_compile.compile(str(script_path), doraise=True)
from pathlib import Path
import py_compile


def test_analyze_script_compiles() -> None:
    py_compile.compile(Path("scripts/analyze.py"), doraise=True)
