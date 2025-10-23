from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


STUB_NORMALIZE_SOURCE = """from __future__ import annotations

import argparse
import os
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    record_path = Path(os.environ["EVAL_SMOKE_RECORD_PATH"])
    record_path.parent.mkdir(parents=True, exist_ok=True)
    with record_path.open("a", encoding="utf-8") as stream:
        stream.write("normalize\\n")

    if args.output:
        Path(args.output).write_text("normalized", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


STUB_EVALUATOR_SOURCE = """from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ruleset", required=True)
    parser.add_argument("--inputs")
    parser.add_argument("--expected")
    parser.add_argument("--output")
    parser.add_argument("extras", nargs="*")
    return parser.parse_args(list(argv) if argv is not None else None)


def _collect_severities(text: str) -> list[str]:
    severities: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("severity:"):
            severities.append(stripped.split(":", 1)[1].strip())
    return severities


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    rules_path = Path(args.ruleset)
    content = rules_path.read_text(encoding="utf-8")
    severities = _collect_severities(content)

    if args.inputs is None:
        raise AssertionError("--inputs must be provided")
    if args.expected is None:
        raise AssertionError("--expected must be provided")
    if args.output is None:
        raise AssertionError("--output must be provided")

    record_path = Path(os.environ["EVAL_SMOKE_RECORD_PATH"])
    record_path.parent.mkdir(parents=True, exist_ok=True)
    with record_path.open("a", encoding="utf-8") as stream:
        stream.write(f"ruleset={rules_path}\\n")
        stream.write("severities=" + ",".join(severities) + "\\n")
        stream.write(f"inputs={args.inputs}\\n")
        stream.write(f"expected={args.expected}\\n")
        stream.write("bert_score\\n")
        stream.write("rouge\\n")

    metrics_arg = args.output or os.environ["EVAL_SMOKE_METRICS_PATH"]
    metrics_path = Path(metrics_arg)
    metrics = {
        "semantic": {
            "bert_score": {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "threshold_met": True,
            }
        },
        "surface": {
            "rouge1": 0.0,
            "rougeL": 0.0,
            "threshold_met": True,
        },
        "violations": {
            "counts": {"minor": 0, "major": 0, "critical": 0},
            "max_severity": severities[-1] if severities else "none",
            "threshold_met": True,
            "violations": [],
        },
        "overall_pass": True,
        "needs_review": False,
        "generated_at": "1970-01-01T00:00:00+00:00",
    }
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


@pytest.fixture()
def stub_quality_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Path:
    real_quality = PROJECT_ROOT / "quality"
    backup_quality = tmp_path / "quality_real"
    real_quality.rename(backup_quality)

    def _restore() -> None:
        if real_quality.is_symlink():
            real_quality.unlink()
        elif real_quality.exists() and real_quality.is_dir():
            shutil.rmtree(real_quality)
        if backup_quality.exists() and not real_quality.exists():
            backup_quality.rename(real_quality)

    request.addfinalizer(_restore)

    stub_root = tmp_path / "stubs"
    quality_root = stub_root / "quality"
    quality_root.mkdir(parents=True, exist_ok=True)

    guardrails_src = backup_quality / "guardrails"
    guardrails_dst = quality_root / "guardrails"
    if guardrails_src.exists():
        shutil.copytree(guardrails_src, guardrails_dst)

    (quality_root / "pipeline").mkdir(parents=True, exist_ok=True)
    (quality_root / "evaluator").mkdir(parents=True, exist_ok=True)

    for package_init in (
        quality_root / "__init__.py",
        quality_root / "pipeline" / "__init__.py",
        quality_root / "evaluator" / "__init__.py",
    ):
        package_init.write_text("", encoding="utf-8")

    (quality_root / "pipeline" / "normalize.py").write_text(
        STUB_NORMALIZE_SOURCE,
        encoding="utf-8",
    )

    (quality_root / "evaluator" / "cli.py").write_text(
        STUB_EVALUATOR_SOURCE,
        encoding="utf-8",
    )

    real_quality.symlink_to(quality_root, target_is_directory=True)

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
    inputs_line = next(line for line in lines if line.startswith("inputs="))
    expected_line = next(line for line in lines if line.startswith("expected="))
    assert inputs_line.endswith("inputs.jsonl")
    assert expected_line.endswith("expected.jsonl")
    assert "bert_score" in lines
    assert "rouge" in lines

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["semantic"]["bert_score"]["threshold_met"] is True
    assert metrics["surface"]["threshold_met"] is True
    assert metrics["violations"]["threshold_met"] is True
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is False
    assert "generated_at" in metrics


def test_eval_smoke_pipeline_with_real_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("bs4")
    pytest.importorskip("quality.pipeline.normalize")
    pytest.importorskip("quality.evaluator.cli")

    record_path = tmp_path / "record.log"
    metrics_path = tmp_path / "metrics.json"
    monkeypatch.setenv("EVAL_SMOKE_RECORD_PATH", str(record_path))
    monkeypatch.setenv("EVAL_SMOKE_METRICS_PATH", str(metrics_path))

    script_path = PROJECT_ROOT / "scripts" / "quality" / "eval_smoke.sh"
    assert script_path.exists(), "eval_smoke.sh must exist for the smoke test"

    try:
        completed = subprocess.run(
            ["bash", str(script_path)],
            check=True,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - diagnostic path
        pytest.fail(f"eval_smoke.sh hung waiting for stdin: {exc}")

    assert completed.returncode == 0
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "semantic" in metrics
    assert "surface" in metrics
