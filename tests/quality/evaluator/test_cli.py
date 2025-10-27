"""quality.evaluator.cli の CLI エントリーポイントテスト."""

from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Sequence

import pytest


class _FakeBERTScorer:
    def __init__(self, *_: Any, **__: Any) -> None:
        self.precisions = [0.91]
        self.recalls = [0.83]
        self.f1s = [0.87]

    def score(self, candidates: Sequence[str], references: Sequence[str]) -> tuple[Iterable[float], Iterable[float], Iterable[float]]:
        assert list(candidates)
        assert list(references)
        return self.precisions, self.recalls, self.f1s


class _FakeRouge:
    def compute(self, *, predictions: Sequence[str], references: Sequence[str], use_stemmer: bool = True) -> dict[str, float]:
        assert use_stemmer
        assert list(predictions)
        assert list(references)
        return {"rouge1": 0.78, "rougeL": 0.72}


@pytest.fixture(autouse=True)
def _stub_third_party(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bert_score", SimpleNamespace(BERTScorer=_FakeBERTScorer))
    monkeypatch.setitem(sys.modules, "evaluate", SimpleNamespace(load=lambda name: _FakeRouge()))
    monkeypatch.setitem(sys.modules, "rouge_score", SimpleNamespace())


def test_collect_pairs_preserves_zero_like_values(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text(
        "\n".join(
            [
                "{\"id\": \"0\", \"output\": 0}",
                "{\"id\": \"1\", \"output\": false, \"response\": \"should-not-fallback\"}",
                "{\"id\": \"2\", \"output\": \"\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    expected_path.write_text(
        "\n".join(
            [
                "{\"id\": \"0\", \"expected\": 0}",
                "{\"id\": \"1\", \"expected\": false, \"reference\": \"should-not-fallback\"}",
                "{\"id\": \"2\", \"expected\": \"\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["0", "False", ""]
    assert references == ["0", "False", ""]


def test_collect_pairs_appends_missing_outputs(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text(
        "\n".join(
            [
                "{\"id\": \"present\", \"output\": \"actual\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    expected_path.write_text(
        "\n".join(
            [
                "{\"id\": \"present\", \"expected\": \"expected\"}",
                "{\"id\": \"missing\", \"expected\": \"fallback\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["actual", ""]
    assert references == ["expected", "fallback"]


def test_collect_pairs_skips_missing_identifiers(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text(
        "\n".join(
            [
                "{\"id\": \"keep\", \"output\": \"kept\"}",
                "{\"output\": \"missing-id\"}",
                "{\"id\": null, \"output\": \"null-id\"}",
                "{\"id\": \"\", \"output\": \"empty-id\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    expected_path.write_text(
        "\n".join(
            [
                "{\"id\": \"keep\", \"expected\": \"expected\"}",
                "{\"expected\": \"missing-id\"}",
                "{\"id\": null, \"expected\": \"null-id\"}",
                "{\"id\": \"\", \"expected\": \"empty-id\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["kept"]
    assert references == ["expected"]


def test_collect_pairs_preserves_comma_separated_strings(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text("{'id': '1', 'output': 'alpha, beta'}\n", encoding="utf-8")
    expected_path.write_text("{'id': '1', 'expected': 'gamma, delta'}\n", encoding="utf-8")

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["alpha, beta"]
    assert references == ["gamma, delta"]


def test_collect_pairs_skips_duplicate_identifiers(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text(
        "\n".join(
            [
                "{\"id\": \"dup\", \"output\": \"first\"}",
                "{\"id\": \"dup\", \"output\": \"second\"}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    expected_path.write_text("{\"id\": \"dup\", \"expected\": \"ref\"}\n", encoding="utf-8")

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["first"]
    assert references == ["ref"]


def test_collect_pairs_preserves_single_quote_and_comma_strings(tmp_path: Path) -> None:
    module = import_module("quality.evaluator.cli")

    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"

    inputs_path.write_text("{'id': '1', 'output': 'he\\'s, coming'}\n", encoding="utf-8")
    expected_path.write_text("{'id': '1', 'expected': 'stay\\'s, calm'}\n", encoding="utf-8")

    outputs, references = module._collect_pairs(inputs_path, expected_path)

    assert outputs == ["he's, coming"]
    assert references == ["stay's, calm"]


def test_parse_rules_yaml_strips_wrapping_quotes() -> None:
    module = import_module("quality.evaluator.cli")

    parsed = module._parse_rules_yaml(
        """
version: 1
rules:
  - id: rule-contains
    severity: minor
    any:
      - contains: "TODO"
      - contains: 'FIXME'
"""
    )

    rule = parsed["rules"][0]

    assert module._matches_rule(rule, "TODO: double quoted")
    assert module._matches_rule(rule, "FIXME: single quoted")
    assert not module._matches_rule(rule, "NOTE: no match")


def test_cli_outputs_expected_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 1, "major": 0, "critical": 0},
            "violations": [
                {
                    "id": "content.minor.placeholder",
                    "severity": "minor",
                    "message": "stubbed",
                }
            ],
            "max_severity": "minor",
        }

    monkeypatch.setattr(module, "_evaluate_guardrails", _fake_guardrail)

    argv = [
        "quality-evaluator",
        "--ruleset",
        str(rules_path),
        "--inputs",
        str(inputs_path),
        "--expected",
        str(expected_path),
        "--output",
        str(metrics_path),
    ]

    exit_code = module.main(argv)

    assert exit_code == 0
    assert metrics_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["semantic"]["bert_score"] == {
        "precision": 0.91,
        "recall": 0.83,
        "f1": 0.87,
        "threshold_met": True,
    }
    assert metrics["surface"] == {"rouge1": 0.78, "rougeL": 0.72, "threshold_met": True}
    assert metrics["violations"]["counts"] == {"minor": 1, "major": 0, "critical": 0}
    assert metrics["violations"]["violations"][0]["severity"] == "minor"
    assert metrics["violations"]["threshold_met"] is True
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is False
    assert isinstance(metrics["generated_at"], str)


def test_cli_generates_metrics_when_missing_in_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_path = tmp_path / "bundle"
    bundle_path.mkdir()
    metrics_path = bundle_path / "metrics.json"
    inputs_path = bundle_path / "inputs.jsonl"
    expected_path = bundle_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 0, "critical": 0},
            "violations": [],
            "max_severity": "none",
        }

    monkeypatch.setattr(module, "_evaluate_guardrails", _fake_guardrail)

    assert not metrics_path.exists()

    argv = [
        "--ruleset",
        str(rules_path),
        str(bundle_path),
    ]

    exit_code = module.main(argv)

    assert exit_code == 0
    assert metrics_path.exists()


def test_cli_treats_single_metric_threshold_as_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{\"id\": \"0\", \"output\": \"hello\"}\n", encoding="utf-8")
    expected_path.write_text("{\"id\": \"0\", \"expected\": \"world\"}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 0, "critical": 0},
            "violations": [],
            "max_severity": "none",
        }

    monkeypatch.setattr(module, "_evaluate_guardrails", _fake_guardrail)
    monkeypatch.setattr(
        module,
        "_evaluate_surface",
        lambda *_: {"rouge1": 0.6, "rougeL": 0.6},
    )

    argv = [
        "quality-evaluator",
        "--ruleset",
        str(rules_path),
        "--inputs",
        str(inputs_path),
        "--expected",
        str(expected_path),
        "--output",
        str(metrics_path),
    ]

    exit_code = module.main(argv)

    assert exit_code == 0
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert metrics["semantic"]["bert_score"]["threshold_met"] is True
    assert metrics["surface"]["threshold_met"] is False
    assert metrics["violations"]["threshold_met"] is True
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is True
    assert isinstance(metrics["generated_at"], str)


def test_cli_fails_on_critical_violation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 0, "critical": 1},
            "violations": [
                {
                    "id": "content.critical.placeholder",
                    "severity": "critical",
                    "message": "stubbed",
                }
            ],
            "max_severity": "critical",
        }

    monkeypatch.setattr(module, "_evaluate_guardrails", _fake_guardrail)

    argv = [
        "quality-evaluator",
        "--ruleset",
        str(rules_path),
        "--inputs",
        str(inputs_path),
        "--expected",
        str(expected_path),
        "--output",
        str(metrics_path),
    ]

    exit_code = module.main(argv)

    assert exit_code == 1
    assert metrics_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["violations"]["max_severity"] == "critical"
    assert metrics["violations"]["threshold_met"] is False
    assert metrics["overall_pass"] is False
    assert metrics["needs_review"] is True
