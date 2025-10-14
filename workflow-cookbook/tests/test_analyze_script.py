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
