from pathlib import Path
from typing import IO, Any, Dict

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test envs without PyYAML
    class _MiniYAML:
        def safe_load(self, stream: IO[str] | str) -> Dict[str, Any]:
            if hasattr(stream, "read"):
                content = stream.read()
            else:
                content = str(stream)

            root: Dict[str, Any] = {}
            stack: list[Dict[str, Any]] = [root]
            indents = [0]

            for raw_line in content.splitlines():
                stripped = raw_line.lstrip()
                if not stripped or stripped.startswith("#"):
                    continue

                indent = len(raw_line) - len(stripped)
                key, _, value = stripped.partition(":")
                value = value.strip()

                while indent < indents[-1]:
                    stack.pop()
                    indents.pop()

                if value == "":
                    new_map: Dict[str, Any] = {}
                    stack[-1][key] = new_map
                    stack.append(new_map)
                    indents.append(indent + 2)
                else:
                    if value.startswith("\"") and value.endswith("\""):
                        value = value[1:-1]
                    stack[-1][key] = value

            return root

    yaml = _MiniYAML()  # type: ignore


def load_workflow(name: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    workflow_path = root / ".github" / "workflows" / name
    with workflow_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_reflection_manifest_path() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"
    assert (
        reflection_manifest.exists()
    ), "workflow-cookbook/reflection.yaml が存在する必要があります"


def test_workflow_defaults_run_working_directory() -> None:
    for workflow_name in ("test.yml", "reflection.yml"):
        workflow = load_workflow(workflow_name)
        assert workflow["defaults"]["run"]["working-directory"] == "workflow-cookbook"


def test_reflection_manifest_present_for_workflow_defaults() -> None:
    reflection_manifest = Path(__file__).resolve().parents[1] / "reflection.yaml"
    assert (
        reflection_manifest.exists()
    ), "workflow-cookbook/reflection.yaml が存在する必要があります"
