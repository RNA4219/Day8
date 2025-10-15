from __future__ import annotations

import re
from pathlib import Path


def test_reflection_manifest_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"
    assert reflection_manifest.exists(), "workflow-cookbook/reflection.yaml が存在する必要があります"


def test_reflection_manifest_paths() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"

    manifest_text = reflection_manifest.read_text(encoding="utf-8")

    target_logs_pattern = re.compile(
        r"targets:\s*-\s+name:\s*unit\s+logs:\s*\[\s*\"([^\"]+)\"\s*\]",
        flags=re.MULTILINE,
    )
    target_logs_match = target_logs_pattern.search(manifest_text)
    assert target_logs_match, "targets[0].logs が定義されている必要があります"
    assert (
        target_logs_match.group(1) == "logs/test.jsonl"
    ), "targets[0].logs は logs/test.jsonl を指す必要があります"

    report_output_pattern = re.compile(
        r"report:\s+output:\s*\"([^\"]+)\"",
        flags=re.MULTILINE,
    )
    report_output_match = report_output_pattern.search(manifest_text)
    assert report_output_match, "report.output が定義されている必要があります"
    assert (
        report_output_match.group(1) == "reports/today.md"
    ), "report.output は reports/today.md を指す必要があります"
