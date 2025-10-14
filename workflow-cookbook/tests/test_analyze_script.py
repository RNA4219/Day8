import py_compile
from pathlib import Path


def test_analyze_script_compiles() -> None:
    py_compile.compile(Path("scripts/analyze.py"), doraise=True)
