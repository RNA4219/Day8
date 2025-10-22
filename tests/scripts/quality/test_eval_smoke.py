from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Iterable

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def stub_quality_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    stub_root = tmp_path / "stubs"
    (stub_root / "quality" / "pipeline").mkdir(parents=True, exist_ok=True)
    (stub_root / "quality" / "evaluator").mkdir(parents=True, exist_ok=True)

    for package_init in (
        stub_root / "quality" / "__init__.py",
        stub_root / "quality" / "pipeline" / "__init__.py",
        stub_root / "quality" / "evaluator" / "__init__.py",
    ):
        package_init.write_text("", encoding="utf-8")

    (stub_root / "quality" / "pipeline" / "normalize.py").write_text(
        """from __future__ import annotations\n\nimport os\nfrom pathlib import Path\n\n\ndef main() -> None:\n    record_path = Path(os.environ[\"EVAL_SMOKE_RECORD_PATH\"])\n    record_path.parent.mkdir(parents=True, exist_ok=True)\n    with record_path.open(\"a\", encoding=\"utf-8\") as stream:\n        stream.write(\"normalize\\n\")\n\n\nif __name__ == \"__main__\":\n    main()\n""",
        encoding="utf-8",
    )

    (stub_root / "quality" / "evaluator" / "cli.py").write_text(
        """from __future__ import annotations\n\nimport argparse\nimport json\nimport os\nfrom pathlib import Path\nfrom typing import Iterable\n\n\ndef parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:\n    parser = argparse.ArgumentParser()\n    parser.add_argument(\"--ruleset\", required=True)\n    parser.add_argument(\"inputs\", nargs=\"*\")\n    return parser.parse_args(list(argv) if argv is not None else None)\n\n\ndef _collect_severities(text: str) -> list[str]:\n    severities: list[str] = []\n    for line in text.splitlines():\n        stripped = line.strip()\n        if stripped.startswith(\"severity:\"):\n            severities.append(stripped.split(\":\", 1)[1].strip())\n    return severities\n\n\ndef main(argv: Iterable[str] | None = None) -> int:\n    args = parse_args(argv)\n    rules_path = Path(args.ruleset)\n    content = rules_path.read_text(encoding=\"utf-8\")\n    severities = _collect_severities(content)\n\n    record_path = Path(os.environ[\"EVAL_SMOKE_RECORD_PATH\"])\n    record_path.parent.mkdir(parents=True, exist_ok=True)\n    with record_path.open(\"a\", encoding=\"utf-8\") as stream:\n        stream.write(f\"ruleset={rules_path}\\n\")\n        stream.write(\"severities=\" + ",".join(severities) + \"\\n\")\n        stream.write(\"bert_score\\n\")\n        stream.write(\"rouge\\n\")\n\n    metrics_path = Path(os.environ[\"EVAL_SMOKE_METRICS_PATH\"])\n    metrics = {\n        \"semantic\": {\"f1\": 0.0, \"threshold_met\": True},\n        \"surface\": {\"rougeL\": 0.0, \"threshold_met\": True},\n        \"violations\": {\"max_severity\": severities[-1] if severities else \"\"},\n    }\n    metrics_path.write_text(json.dumps(metrics), encoding=\"utf-8\")\n    return 0\n\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n""",
        encoding="utf-8",
    )

    existing = os.environ.get("PYTHONPATH")
    new_path = str(stub_root) if not existing else f"{stub_root}{os.pathsep}{existing}"
    monkeypatch.setenv("PYTHONPATH", new_path)
    return stub_root


def test_eval_smoke_pipeline_invokes_stubs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stub_quality_modules: Path
) -> None:
    record_path = tmp_path / "record.log"
    metrics_path = tmp_path / "metrics.json"
    monkeypatch.setenv("EVAL_SMOKE_RECORD_PATH", str(record_path))
    monkeypatch.setenv("EVAL_SMOKE_METRICS_PATH", str(metrics_path))

    script_path = PROJECT_ROOT / "scripts" / "quality" / "eval_smoke.sh"
    assert script_path.exists(), "eval_smoke.sh must exist for the smoke test"

    completed = subprocess.run(
        ["bash", str(script_path)],
        check=True,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert record_path.exists()
    lines = record_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "normalize"
    severity_line = next(line for line in lines if line.startswith("severities="))
    assert severity_line == "severities=minor,major,critical"
    assert "bert_score" in lines
    assert "rouge" in lines

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["semantic"]["threshold_met"] is True
    assert metrics["surface"]["threshold_met"] is True
