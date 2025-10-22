"""quality.evaluator.cli の CLI エントリーポイントテスト."""

from __future__ import annotations

import json
from datetime import datetime
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
        return {"rouge1": 0.42, "rougeL": 0.38}


@pytest.fixture(autouse=True)
def _stub_third_party(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bert_score", SimpleNamespace(BERTScorer=_FakeBERTScorer))
    monkeypatch.setitem(sys.modules, "evaluate", SimpleNamespace(load=lambda name: _FakeRouge()))
    monkeypatch.setitem(sys.modules, "rouge_score", SimpleNamespace())


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
    assert metrics["surface"] == {"rouge1": 0.42, "rougeL": 0.38, "threshold_met": False}
    assert metrics["violations"]["counts"] == {"minor": 1, "major": 0, "critical": 0}
    assert metrics["violations"]["violations"][0]["severity"] == "minor"
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is False
    assert isinstance(metrics["generated_at"], str)
    # ISO8601 形式の整合性チェック
    datetime.fromisoformat(metrics["generated_at"].replace("Z", "+00:00"))


def test_cli_overall_fail_with_critical_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    assert exit_code == 0
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["overall_pass"] is False
    assert metrics["needs_review"] is False


def test_cli_overall_needs_review_when_thresholds_not_met(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _LowScoreBERTScorer(_FakeBERTScorer):
        def __init__(self, *_: Any, **__: Any) -> None:
            super().__init__()
            self.precisions = [0.6]
            self.recalls = [0.55]
            self.f1s = [0.58]

    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    monkeypatch.setattr(
        sys.modules["bert_score"],
        "BERTScorer",
        _LowScoreBERTScorer,
    )

    def _no_violation(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 0, "critical": 0},
            "violations": [],
            "max_severity": "none",
        }

    monkeypatch.setattr(module, "_evaluate_guardrails", _no_violation)

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
    assert metrics["semantic"]["bert_score"]["threshold_met"] is False
    assert metrics["surface"]["threshold_met"] is False
    assert metrics["overall_pass"] is False
    assert metrics["needs_review"] is True
