"""Quality evaluator CLI."""

from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

_UNQUOTED_KEY_PATTERN = re.compile(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)')
_JSON_LITERAL_PATTERN = re.compile(r'(:\s*)(true|false|null)(?=\s*(?:[,}]))', re.IGNORECASE)
_BARE_WORD_PATTERN = re.compile(r'(:\s*)([A-Za-z_][A-Za-z0-9_-]*)(?=\s*(?:[,}]))')

_SEVERITY_PRIORITY = {"critical": 3, "major": 2, "minor": 1}
_BERT_F1_THRESHOLD = 0.85
_ROUGE_L_THRESHOLD = 0.70


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Day8 quality metrics")
    parser.add_argument("bundle", nargs="?", help="入力・期待値・出力が置かれたディレクトリ")
    parser.add_argument("--ruleset", required=True, help="Guardrails ルールセット YAML のパス")
    parser.add_argument("--inputs", help="モデル出力 JSONL のパス")
    parser.add_argument("--expected", help="期待値 JSONL のパス")
    parser.add_argument("--output", help="メトリクス JSON の出力先")
    return parser.parse_args(list(argv) if argv is not None else None)


def _resolve_path(
    raw: str | None, bundle: Path | None, default_name: str, *, allow_missing: bool = False
) -> Path | None:
    if raw:
        return Path(raw)
    if bundle and bundle.is_dir():
        candidate = bundle / default_name
        if allow_missing or candidate.exists():
            return candidate
    return None


def _load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            records.append(_parse_loose_mapping(raw))
    return records


def _parse_loose_mapping(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if not candidate:
        return {}

    if not (candidate.startswith("{") and candidate.endswith("}")):
        core = candidate.strip().strip("{}")
        candidate = "{" + core + "}"

    def _literal_eval_mapping(payload: str) -> dict[str, Any] | None:
        try:
            parsed = ast.literal_eval(payload)
        except (SyntaxError, ValueError):
            return None
        if not isinstance(parsed, dict):
            return None
        return {str(key): value for key, value in parsed.items()}

    attempts: list[str] = [candidate]

    sanitized = _UNQUOTED_KEY_PATTERN.sub(
        lambda match: f"{match.group(1)}'{match.group(2)}'{match.group(3)}",
        candidate,
    )
    sanitized = _JSON_LITERAL_PATTERN.sub(
        lambda match: match.group(1)
        + {"true": "True", "false": "False", "null": "None"}[match.group(2).lower()],
        sanitized,
    )
    sanitized = _BARE_WORD_PATTERN.sub(
        lambda match: match.group(0)
        if match.group(2).lower() in {"true", "false", "none"}
        else f"{match.group(1)}'{match.group(2)}'",
        sanitized,
    )
    if sanitized not in attempts:
        attempts.append(sanitized)

    for payload in attempts:
        literal = _literal_eval_mapping(payload)
        if literal is not None:
            return literal

    return {}


def _collect_pairs(inputs: Path, expected: Path) -> tuple[list[str], list[str]]:
    def _select_text(record: dict[str, Any], candidates: Sequence[str]) -> str:
        for candidate in candidates:
            if candidate in record:
                value = record[candidate]
                if value is not None:
                    return str(value)
        return ""

    expected_map: dict[str, tuple[str, bool]] = {}
    for item in _load_records(expected):
        raw_id = item.get("id")
        if raw_id is None:
            continue
        if isinstance(raw_id, str) and raw_id == "":
            continue
        key = str(raw_id)
        expected_map[key] = (_select_text(item, ("expected", "reference")), False)

    outputs: list[str] = []
    references: list[str] = []
    for record in _load_records(inputs):
        raw_id = record.get("id")
        if raw_id is None:
            continue
        if isinstance(raw_id, str) and raw_id == "":
            continue
        key = str(raw_id)
        if key not in expected_map:
            continue
        reference, matched = expected_map[key]
        if matched:
            continue
        outputs.append(_select_text(record, ("output", "response")))
        references.append(reference)
        expected_map[key] = (reference, True)
    for reference, matched in expected_map.values():
        if matched:
            continue
        outputs.append("")
        references.append(reference)
    return outputs, references


def _mean(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    return sum(numbers) / len(numbers) if numbers else 0.0


def _evaluate_semantic(outputs: Sequence[str], references: Sequence[str]) -> dict[str, float]:
    if not outputs or not references:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    from bert_score import BERTScorer

    scorer = BERTScorer(lang="en", rescale_with_baseline=True)
    precisions, recalls, f1s = scorer.score(outputs, references)
    return {
        "precision": round(_mean(precisions), 4),
        "recall": round(_mean(recalls), 4),
        "f1": round(_mean(f1s), 4),
    }


def _evaluate_surface(outputs: Sequence[str], references: Sequence[str]) -> dict[str, float]:
    if not outputs or not references:
        return {"rouge1": 0.0, "rougeL": 0.0}
    import evaluate

    rouge = evaluate.load("rouge")
    result = rouge.compute(predictions=list(outputs), references=list(references), use_stemmer=True)
    return {
        "rouge1": round(float(result.get("rouge1", 0.0)), 4),
        "rougeL": round(float(result.get("rougeL", 0.0)), 4),
    }


def _apply_thresholds(
    bert_score: dict[str, float], surface_metrics: dict[str, float]
) -> tuple[dict[str, Any], dict[str, Any]]:
    bert_with_threshold = dict(bert_score)
    bert_with_threshold["threshold_met"] = bert_with_threshold.get("f1", 0.0) >= _BERT_F1_THRESHOLD

    surface_with_threshold = dict(surface_metrics)
    surface_with_threshold["threshold_met"] = surface_with_threshold.get("rougeL", 0.0) >= _ROUGE_L_THRESHOLD
    return bert_with_threshold, surface_with_threshold


def _apply_violation_threshold(violations: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(violations)
    severity = str(normalized.get("max_severity", "none")).lower()
    normalized["max_severity"] = severity
    normalized["threshold_met"] = severity != "critical"
    return normalized


def _load_ruleset(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ModuleNotFoundError:
        return _parse_rules_yaml(text)


def _parse_rules_yaml(text: str) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    gathering_contains = False
    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped in {"rules", "rules:"}:
            idx += 1
            continue
        if stripped.startswith("- id:"):
            if current:
                rules.append(current)
            current = {"id": stripped.split(":", 1)[1].strip(), "match": {"any": []}}
            gathering_contains = False
            idx += 1
            continue
        if current is None:
            idx += 1
            continue
        if stripped.startswith("description:"):
            current["description"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("severity:"):
            current["severity"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("any:"):
            gathering_contains = True
            idx += 1
            continue
        elif stripped.startswith("- contains:") and gathering_contains:
            payload = stripped.split(":", 1)[1].strip()
            indent_level = len(raw) - len(raw.lstrip(" "))
            if payload.startswith("|") or payload.startswith(">"):
                idx += 1
                block_lines: list[tuple[str, int | None]] = []
                while idx < len(lines):
                    candidate_raw = lines[idx]
                    candidate_stripped = candidate_raw.strip()
                    candidate_indent = len(candidate_raw) - len(candidate_raw.lstrip(" "))
                    if candidate_stripped == "":
                        block_lines.append(("", None))
                        idx += 1
                        continue
                    if candidate_indent <= indent_level:
                        break
                    block_lines.append((candidate_raw, candidate_indent))
                    idx += 1
                contents: list[str] = []
                if block_lines:
                    indents = [indent for _, indent in block_lines if indent is not None]
                    trim_indent = min(indents) if indents else indent_level + 1
                    for line, indent in block_lines:
                        if indent is None:
                            contents.append("")
                        else:
                            start = trim_indent if len(line) >= trim_indent else len(line)
                            contents.append(line[start:])
                value = "\n".join(contents) if payload.startswith("|") else " ".join(
                    segment for segment in (part.strip() for part in contents) if segment
                )
                match = current.setdefault("match", {})
                match.setdefault("any", []).append({"contains": value})
                continue
            if len(payload) >= 2 and payload[0] == payload[-1] and payload[0] in {'"', "'"}:
                payload = payload[1:-1]
            match = current.setdefault("match", {})
            match.setdefault("any", []).append({"contains": payload})
            idx += 1
            continue
        elif not raw.startswith("  "):
            gathering_contains = False
        idx += 1
    if current:
        rules.append(current)
    return {"rules": rules}


def _matches_rule(rule: dict[str, Any], text: str) -> bool:
    any_nodes = rule.get("match", {}).get("any", [])
    return any(
        isinstance(node, dict) and node.get("contains") and node["contains"] in text
        for node in any_nodes
    )


def _evaluate_guardrails(ruleset_path: Path, outputs: Sequence[str]) -> dict[str, Any]:
    counts = {severity: 0 for severity in _SEVERITY_PRIORITY}
    if not outputs:
        return {"counts": counts, "violations": [], "max_severity": "none"}

    loaded = _load_ruleset(ruleset_path)
    violations: list[dict[str, Any]] = []
    for rule in loaded.get("rules", []):
        severity = str(rule.get("severity", "")).lower()
        if severity not in counts:
            continue
        if any(_matches_rule(rule, output) for output in outputs):
            counts[severity] += 1
            violations.append(
                {
                    "id": rule.get("id", ""),
                    "severity": severity,
                    "message": rule.get("description", ""),
                }
            )

    max_severity = "none"
    for severity in sorted(counts, key=_SEVERITY_PRIORITY.get, reverse=True):
        if counts[severity] > 0:
            max_severity = severity
            break
    return {"counts": counts, "violations": violations, "max_severity": max_severity}


def _summarize_results(
    bert_score: dict[str, Any], surface_metrics: dict[str, Any], violations: dict[str, Any]
) -> dict[str, Any]:
    bert_pass = bool(bert_score.get("threshold_met"))
    rouge_pass = bool(surface_metrics.get("threshold_met"))
    severity = str(violations.get("max_severity", "none"))
    severity_score = _SEVERITY_PRIORITY.get(severity, 0)
    rules_pass = severity != "critical"
    overall_pass = rules_pass and (bert_pass or rouge_pass)
    needs_review = (
        not overall_pass
        or not (bert_pass and rouge_pass)
        or severity_score >= _SEVERITY_PRIORITY.get("major", 0)
    )
    return {
        "overall_pass": overall_pass,
        "needs_review": needs_review,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    bundle = Path(args.bundle) if args.bundle else None

    inputs_path = _resolve_path(args.inputs, bundle, "inputs.jsonl")
    expected_path = _resolve_path(args.expected, bundle, "expected.jsonl")
    output_path = _resolve_path(args.output, bundle, "metrics.json", allow_missing=True)
    if not inputs_path or not expected_path or not output_path:
        raise SystemExit("inputs, expected, output を指定してください")

    outputs, references = _collect_pairs(inputs_path, expected_path)
    bert_score = _evaluate_semantic(outputs, references)
    surface_metrics = _evaluate_surface(outputs, references)
    bert_score_with_threshold, surface_with_threshold = _apply_thresholds(bert_score, surface_metrics)
    violations = _apply_violation_threshold(
        _evaluate_guardrails(Path(args.ruleset), outputs)
    )
    summary = _summarize_results(bert_score_with_threshold, surface_with_threshold, violations)

    metrics = {
        "semantic": {"bert_score": bert_score_with_threshold},
        "surface": surface_with_threshold,
        "violations": violations,
        **summary,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
