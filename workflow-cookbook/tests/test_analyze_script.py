from pathlib import Path
import py_compile


def test_analyze_script_compiles() -> None:
    py_compile.compile(Path("scripts/analyze.py"), doraise=True)
