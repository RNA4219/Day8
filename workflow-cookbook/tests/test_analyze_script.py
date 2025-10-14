import py_compile
from pathlib import Path


def test_analyze_script_compiles() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "analyze.py"
    py_compile.compile(str(script_path), doraise=True)
