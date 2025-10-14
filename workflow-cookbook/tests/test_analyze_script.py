from __future__ import annotations

from pathlib import Path
import py_compile
import tempfile


def test_analyze_script_compiles() -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "analyze.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        cfile = Path(tmpdir) / "analyze.pyc"
        compiled_path = py_compile.compile(
            str(script_path),
            cfile=str(cfile),
            doraise=True,
        )
        assert Path(compiled_path).exists()
