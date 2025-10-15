from pathlib import Path


def test_reflection_manifest_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"
    assert reflection_manifest.exists(), "workflow-cookbook/reflection.yaml が存在する必要があります"
