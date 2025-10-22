"""quality.evaluator.cli の CLI エントリーポイントテスト."""

from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Sequence

import pytest


_BERT_SCORE_PAYLOAD = {
    "precision": [0.91],
    "recall": [0.83],
    "f1": [0.87],
}


class _FakeBERTScorer:
    def __init__(self, *_: Any, **__: Any) -> None:
        self.precisions = list(_BERT_SCORE_PAYLOAD["precision"])
        self.recalls = list(_BERT_SCORE_PAYLOAD["recall"])
        self.f1s = list(_BERT_SCORE_PAYLOAD["f1"])

    def score(self, candidates: Sequence[str], references: Sequence[str]) -> tuple[Iterable[float], Iterable[float], Iterable[float]]:
        assert list(candidates)
        assert list(references)
        return self.precisions, self.recalls, self.f1s


_ROUGE_PAYLOAD = {"rouge1": 0.42, "rougeL": 0.38}


class _FakeRouge:
    def compute(self, *, predictions: Sequence[str], references: Sequence[str], use_stemmer: bool = True) -> dict[str, float]:
        assert use_stemmer
        assert list(predictions)
        assert list(references)
        return dict(_ROUGE_PAYLOAD)


@pytest.fixture(autouse=True)
def _stub_third_party(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bert_score", SimpleNamespace(BERTScorer=_FakeBERTScorer))
    monkeypatch.setitem(sys.modules, "evaluate", SimpleNamespace(load=lambda name: _FakeRouge()))
    monkeypatch.setitem(sys.modules, "rouge_score", SimpleNamespace())


@pytest.fixture()
def _restore_scores() -> Iterable[None]:
    yield
    _BERT_SCORE_PAYLOAD.update({
        "precision": [0.91],
        "recall": [0.83],
        "f1": [0.87],
    })
    _ROUGE_PAYLOAD.update({"rouge1": 0.42, "rougeL": 0.38})


def test_cli_outputs_expected_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _restore_scores: Iterable[None]
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
            "counts": {"minor": 1, "major": 0, "critical": 0},
            "violations": [
                {
                    "id": "content.minor.placeholder",
                    "severity": "minor",
                    "message": "stubbed",
                }
            ],
            "max_severity": "minor",
            "threshold_met": True,
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
    assert metrics["semantic"]["bert_score"] == {"precision": 0.91, "recall": 0.83, "f1": 0.87}
    assert metrics["semantic"]["threshold_met"] is True
    assert metrics["surface"]["rouge1"] == 0.42
    assert metrics["surface"]["rougeL"] == 0.38
    assert metrics["surface"]["threshold_met"] is False
    assert metrics["violations"]["counts"] == {"minor": 1, "major": 0, "critical": 0}
    assert metrics["violations"]["violations"][0]["severity"] == "minor"
    assert metrics["violations"]["max_severity"] == "minor"
    assert metrics["violations"]["threshold_met"] is True
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is True
    assert "generated_at" in metrics


def test_cli_thresholds_allow_partial_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _restore_scores: Iterable[None]
) -> None:
    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    _BERT_SCORE_PAYLOAD.update({"precision": [0.5], "recall": [0.6], "f1": [0.58]})
    _ROUGE_PAYLOAD.update({"rouge1": 0.8, "rougeL": 0.75})

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 1, "critical": 0},
            "violations": [
                {
                    "id": "content.major.stub",
                    "severity": "major",
                    "message": "stubbed",
                }
            ],
            "max_severity": "major",
            "threshold_met": True,
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
    assert metrics["semantic"]["threshold_met"] is False
    assert metrics["surface"]["threshold_met"] is True
    assert metrics["violations"]["threshold_met"] is True
    assert metrics["overall_pass"] is True
    assert metrics["needs_review"] is True


def test_cli_fails_on_critical_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _restore_scores: Iterable[None]
) -> None:
    metrics_path = tmp_path / "metrics.json"
    inputs_path = tmp_path / "inputs.jsonl"
    expected_path = tmp_path / "expected.jsonl"
    rules_path = tmp_path / "rules.yaml"

    inputs_path.write_text("{""id"": ""0"", ""output"": ""hello""}\n", encoding="utf-8")
    expected_path.write_text("{""id"": ""0"", ""expected"": ""world""}\n", encoding="utf-8")
    rules_path.write_text("version: 1\nrules: []\n", encoding="utf-8")

    module = import_module("quality.evaluator.cli")

    _BERT_SCORE_PAYLOAD.update({"precision": [0.9], "recall": [0.9], "f1": [0.92]})
    _ROUGE_PAYLOAD.update({"rouge1": 0.8, "rougeL": 0.76})

    def _fake_guardrail(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "counts": {"minor": 0, "major": 0, "critical": 1},
            "violations": [
                {
                    "id": "content.critical.stub",
                    "severity": "critical",
                    "message": "stubbed",
                }
            ],
            "max_severity": "critical",
            "threshold_met": False,
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
    assert metrics["semantic"]["threshold_met"] is True
    assert metrics["surface"]["threshold_met"] is True
    assert metrics["violations"]["threshold_met"] is False
    assert metrics["overall_pass"] is False
    assert metrics["needs_review"] is True
