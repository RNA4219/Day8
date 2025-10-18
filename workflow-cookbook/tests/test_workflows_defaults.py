from pathlib import Path
from typing import IO, Any, Dict, cast

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
                    if value.startswith("[") and value.endswith("]"):
                        items = []
                        raw_items = value[1:-1].split(",") if value[1:-1].strip() else []
                        for raw_item in raw_items:
                            item = raw_item.strip()
                            if item.startswith("\"") and item.endswith("\""):
                                item = item[1:-1]
                            items.append(item)
                        stack[-1][key] = items
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


def test_reflection_manifest_logs_entry() -> None:
    reflection_manifest = Path(__file__).resolve().parents[1] / "reflection.yaml"
    with reflection_manifest.open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file)

    raw_targets = manifest["targets"]
    if isinstance(raw_targets, dict):
        converted_target: Dict[str, Any] = {}
        if "- name" in raw_targets:
            converted_target["name"] = raw_targets["- name"]
        if "logs" in raw_targets:
            converted_target["logs"] = raw_targets["logs"]
        targets: list[Dict[str, Any]] = [converted_target]
    else:
        targets = cast(list[Dict[str, Any]], raw_targets)

    assert targets[0]["logs"] == ["logs/test.jsonl"]


def test_test_workflow_upload_steps_use_unique_names() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow_path = root / ".github" / "workflows" / "test.yml"

    workflow = load_workflow("test.yml")
    jobs = workflow["jobs"]
    raw_text = workflow_path.read_text(encoding="utf-8")

    aggregate_upload_found = False
    unique_assertions = 0
    for job in jobs.values():
        steps = job.get("steps", [])
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("uses") == "actions/upload-artifact@v4":
                config = step.get("with", {})
                if not isinstance(config, dict):
                    continue
                name = config.get("name")
                if name == "test-logs":
                    aggregate_upload_found = True
                    continue
                if isinstance(name, str) and name.startswith("test-logs"):
                    assert name == "test-logs-${{ github.job }}"
                    assert config.get("overwrite") is True
                    unique_assertions += 1

    if not aggregate_upload_found:
        assert "name: test-logs\n          path: logs/**" in raw_text
        assert "overwrite: true" in raw_text
    else:
        assert aggregate_upload_found, "report ジョブで集約済みの test-logs アーティファクトを公開する必要があります"

    if unique_assertions == 0:
        occurrences = raw_text.count("name: test-logs-${{ github.job }}")
        assert occurrences == 5, "各テストジョブは test-logs-${{ github.job }} アーティファクト名を共有する必要があります"
