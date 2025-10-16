from __future__ import annotations

from pathlib import Path

import re


def test_reflection_manifest_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"
    assert reflection_manifest.exists(), "workflow-cookbook/reflection.yaml が存在する必要があります"


def test_reflection_manifest_paths() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reflection_manifest = project_root / "reflection.yaml"

    manifest_text = reflection_manifest.read_text(encoding="utf-8")

    target_logs_pattern = re.compile(
        r"targets:\s*-.*?name:\s*unit.*?logs:\s*(?:\[\s*\"(?P<inline>[^\"]+)\"\s*\]|(?P<block>(?:\n\s*-\s*[\"']?[^\n]+)+))",
        flags=re.DOTALL,
    )
    target_logs_match = target_logs_pattern.search(manifest_text)
    assert target_logs_match, "unit ターゲットの logs が定義されている必要があります"

    logs_value: str | None = target_logs_match.group("inline")
    if logs_value is None:
        block = target_logs_match.group("block")
        assert block is not None, "logs ブロックが取得できません"
        block_match = re.search(r"-\s*[\"']?([^\s\"']+)", block)
        assert block_match, "logs 配列に要素が必要です"
        logs_value = block_match.group(1)

    assert logs_value == "logs/test.jsonl", "targets[0].logs は logs/test.jsonl を指す必要があります"

    report_output_pattern = re.compile(
        r"report:\s+.*?output:\s*\"?([^\s\"']+)\"?",
        flags=re.DOTALL,
    )
    report_output_match = report_output_pattern.search(manifest_text)
    assert report_output_match, "report.output が定義されている必要があります"
    assert (
        report_output_match.group(1) == "reports/today.md"
    ), "report.output は reports/today.md を指す必要があります"
