"""Quality evaluator CLI."""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
import sys

_UNQUOTED_KEY_PATTERN = re.compile(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)')
_JSON_LITERAL_PATTERN = re.compile(r'(:\s*)(true|false|null)(?=\s*(?:[,}]))', re.IGNORECASE)
_BARE_WORD_PATTERN = re.compile(r'(:\s*)([A-Za-z_][A-Za-z0-9_-]*)(?=\s*(?:[,}]))')

_SEVERITY_PRIORITY = {"critical": 3, "major": 2, "minor": 1}
_BERT_MODEL_DEFAULT = "bert-base-multilingual-cased"
_BERT_BATCH_SIZE_DEFAULT = 16
_BERT_F1_THRESHOLD = 0.85
_ROUGE_L_THRESHOLD = 0.70
_SENTENCEPIECE_ENV_VAR = "DAY8_SENTENCEPIECE_MODEL"


@dataclass(frozen=True)
class EvaluationItem:
    output: str
    reference: str
    metadata: dict[str, Any]


def _unescape_yaml_double_quoted(value: str) -> str:
    escape_map = {
        "0": "\0",
        "a": "\a",
        "b": "\b",
        "t": "\t",
        "n": "\n",
        "v": "\v",
        "f": "\f",
        "r": "\r",
        "e": "\x1b",
        '"': '"',
        "\\": "\\",
        "/": "/",
        "N": "\u0085",
        "_": "\u00a0",
        "L": "\u2028",
        "P": "\u2029",
    }

    result: list[str] = []
    i = 0
    length = len(value)
    while i < length:
        char = value[i]
        if char != "\\":
            result.append(char)
            i += 1
            continue

        i += 1
        if i >= length:
            result.append("\\")
            break

        escape_code = value[i]
        i += 1

        if escape_code in {"x", "u", "U"}:
            widths = {"x": 2, "u": 4, "U": 8}
            width = widths[escape_code]
            hex_digits = value[i : i + width]
            if len(hex_digits) == width and all(c in "0123456789abcdefABCDEF" for c in hex_digits):
                result.append(chr(int(hex_digits, 16)))
                i += width
                continue
            result.append("\\" + escape_code)
            continue

        replacement = escape_map.get(escape_code)
        if replacement is not None:
            result.append(replacement)
            continue

        result.append(escape_code)

    return "".join(result)


def _normalize_yaml_scalar(value: str) -> str:
    text = value.strip()
    if not text:
        return ""

    normalized: list[str] = []
    in_single = False
    in_double = False
    escape = False
    for char in text:
        if escape:
            normalized.append(char)
            escape = False
            continue
        if char == "\\" and not in_single:
            escape = True
            normalized.append(char)
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            normalized.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            normalized.append(char)
            continue
        if char == "#" and not in_single and not in_double:
            break
        normalized.append(char)

    result = "".join(normalized).rstrip()
    if len(result) >= 2 and result[0] == result[-1] and result[0] in {'"', "'"}:
        quote = result[0]
        core = result[1:-1]
        if quote == "'":
            return core.replace("''", "'")
        return _unescape_yaml_double_quoted(core)

    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Day8 quality metrics")
    parser.add_argument("bundle", nargs="?", help="入力・期待値・出力が置かれたディレクトリ")
    parser.add_argument("--ruleset", required=True, help="Guardrails ルールセット YAML のパス")
    parser.add_argument("--inputs", help="モデル出力 JSONL のパス")
    parser.add_argument("--expected", help="期待値 JSONL のパス")
    parser.add_argument("--output", help="メトリクス JSON の出力先")
    parser.add_argument(
        "--bert-model",
        default=_BERT_MODEL_DEFAULT,
        help="BERTScore のモデルタイプ (default: %(default)s)",
    )
    parser.add_argument(
        "--bert-batch-size",
        type=int,
        default=_BERT_BATCH_SIZE_DEFAULT,
        help="BERTScore 計算時のバッチサイズ",
    )
    parser.add_argument(
        "--sentencepiece-model",
        help="ROUGE 計算に使用する SentencePiece モデルのパス",
    )
    parser.add_argument(
        "--generated-at",
        help="metrics.json の generated_at へ記録するリビジョンやタイムスタンプ",
    )
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


def _collect_pairs(inputs: Path, expected: Path) -> list[EvaluationItem]:
    def _select_text(record: dict[str, Any], candidates: Sequence[str]) -> str:
        for candidate in candidates:
            if candidate in record:
                value = record[candidate]
                if value is not None:
                    return str(value)
        return ""

    def _extract_metadata(record: dict[str, Any]) -> dict[str, Any]:
        aggregated: dict[str, Any] = {}
        raw_metadata = record.get("metadata")
        if isinstance(raw_metadata, dict):
            for key, value in raw_metadata.items():
                if value is not None:
                    aggregated[str(key)] = value
        for key, value in record.items():
            if key in {"id", "output", "response", "expected", "reference", "metadata"}:
                continue
            if value is None:
                continue
            aggregated[str(key)] = value
        return aggregated

    expected_map: dict[str, dict[str, Any]] = {}
    for item in _load_records(expected):
        raw_id = item.get("id")
        if raw_id is None:
            continue
        if isinstance(raw_id, str) and raw_id == "":
            continue
        key = str(raw_id)
        expected_map[key] = {
            "reference": _select_text(item, ("expected", "reference")),
            "metadata": _extract_metadata(item),
            "matched": False,
        }

    items: list[EvaluationItem] = []
    for record in _load_records(inputs):
        raw_id = record.get("id")
        if raw_id is None:
            continue
        if isinstance(raw_id, str) and raw_id == "":
            continue
        key = str(raw_id)
        entry = expected_map.get(key)
        if not entry:
            continue
        if entry["matched"]:
            continue
        metadata = dict(entry["metadata"])
        metadata.update(_extract_metadata(record))
        items.append(
            EvaluationItem(
                output=_select_text(record, ("output", "response")),
                reference=str(entry["reference"]),
                metadata=metadata,
            )
        )
        entry["matched"] = True
        entry["metadata"] = metadata

    for entry in expected_map.values():
        if entry["matched"]:
            continue
        items.append(
            EvaluationItem(
                output="",
                reference=str(entry["reference"]),
                metadata=dict(entry["metadata"]),
            )
        )
    return items


def _extract_outputs(items: Sequence[EvaluationItem]) -> list[str]:
    return [item.output for item in items]


def _extract_references(items: Sequence[EvaluationItem]) -> list[str]:
    return [item.reference for item in items]


def _mean(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    return sum(numbers) / len(numbers) if numbers else 0.0


def _detect_torch_device() -> str:
    spec = importlib.util.find_spec("torch")
    if spec is None:
        return "cpu"
    torch = importlib.import_module("torch")
    cuda = getattr(torch, "cuda", None)
    if cuda is not None and callable(getattr(cuda, "is_available", None)):
        return "cuda" if cuda.is_available() else "cpu"
    return "cpu"


def _select_sentencepiece_candidate(raw: str, bundle: Path | None) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute() and bundle is not None:
        bundled = bundle / raw
        if bundled.exists():
            return bundled
    return candidate


def _resolve_sentencepiece_model_path(
    raw: str | None, bundle: Path | None
) -> Path | None:
    if raw:
        return _select_sentencepiece_candidate(raw, bundle)
    env_value = os.environ.get(_SENTENCEPIECE_ENV_VAR)
    if env_value:
        return _select_sentencepiece_candidate(env_value, bundle)
    default_path = Path(__file__).with_name("sentencepiece.model")
    if default_path.exists():
        return default_path
    return None


@lru_cache(maxsize=1)
def _get_janome_tokenizer() -> Any | None:
    try:
        spec = importlib.util.find_spec("janome.tokenizer")
    except ValueError:
        spec = None
    if spec is not None:
        module = importlib.import_module("janome.tokenizer")
        return module.Tokenizer()
    module = sys.modules.get("janome.tokenizer")
    if module is None:
        return None
    tokenizer_factory = getattr(module, "Tokenizer", None)
    if callable(tokenizer_factory):
        return tokenizer_factory()
    return None
def _stem_japanese_segments(segments: Iterable[str]) -> list[str]:
    tokenizer = _get_janome_tokenizer()
    normalized: list[str] = []
    for segment in segments:
        cleaned = segment.replace("▁", " ").strip()
        if not cleaned:
            continue
        if tokenizer is None:
            normalized.append(cleaned.lower())
            continue
        tokens = list(tokenizer.tokenize(cleaned))
        if not tokens:
            normalized.append(cleaned.lower())
            continue
        for token in tokens:
            base_form = getattr(token, "base_form", "")
            surface = getattr(token, "surface", "")
            chosen = base_form if base_form and base_form != "*" else surface
            stripped = str(chosen).strip()
            if stripped:
                normalized.append(stripped.lower())
    return normalized


def _sentencepiece_tokenizer(sp_tokenizer: Any) -> Callable[[str], list[str]]:
    def _coerce_tokens(raw_tokens: Any) -> list[str]:
        if isinstance(raw_tokens, (list, tuple)):
            return [str(token) for token in raw_tokens]
        tokens_attr = getattr(raw_tokens, "tokens", None)
        if tokens_attr is not None:
            return [str(token) for token in tokens_attr]
        return [str(raw_tokens)]

    def _tokenize(text: str) -> list[str]:
        encode_fn = getattr(sp_tokenizer, "encode", None)
        encode_as_pieces_fn = getattr(sp_tokenizer, "encode_as_pieces", None)
        tokens_source: Any
        if callable(encode_fn):
            try:
                tokens_source = encode_fn(text, out_type=str)
            except TypeError:
                if callable(encode_as_pieces_fn):
                    tokens_source = encode_as_pieces_fn(text)
                else:
                    tokens_source = encode_fn(text)
        elif callable(encode_as_pieces_fn):
            tokens_source = encode_as_pieces_fn(text)
        else:
            tokens_source = [text]
        tokens = _coerce_tokens(tokens_source)
        return _stem_japanese_segments(tokens)

    return _tokenize


def _fallback_surface_tokenizer() -> Callable[[str], list[str]]:
    def _tokenize(text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []
        segments = stripped.split()
        if not segments:
            segments = [stripped]
        return _stem_japanese_segments(segments)

    return _tokenize


def _build_surface_tokenizer(sentencepiece_model: Path | None) -> Callable[[str], list[str]]:
    if sentencepiece_model and sentencepiece_model.exists():
        try:
            sp_spec = importlib.util.find_spec("sentencepiece")
        except ValueError:
            sp_spec = None
        sp_module: Any | None = None
        if sp_spec is not None:
            sp_module = importlib.import_module("sentencepiece")
        else:
            sp_module = sys.modules.get("sentencepiece")
        if sp_module is not None:
            sp_cls = getattr(sp_module, "SentencePieceProcessor", None)
            if sp_cls is not None:
                try:
                    try:
                        sp_tokenizer = sp_cls(model_file=str(sentencepiece_model))
                    except TypeError:
                        sp_tokenizer = sp_cls()
                        load = getattr(sp_tokenizer, "load", None)
                        if not callable(load):
                            raise TypeError("SentencePieceProcessor missing load method")
                        load(str(sentencepiece_model))
                    return _sentencepiece_tokenizer(sp_tokenizer)
                except Exception:
                    pass
        try:
            spec = importlib.util.find_spec("tokenizers")
        except ValueError:
            spec = None
        module: Any | None = None
        if spec is not None:
            module = importlib.import_module("tokenizers")
        else:
            module = sys.modules.get("tokenizers")
        if module is not None:
            tokenizer_cls = getattr(module, "Tokenizer", None)
            from_file = getattr(tokenizer_cls, "from_file", None) if tokenizer_cls is not None else None
            if callable(from_file):
                try:
                    sp_tokenizer = from_file(str(sentencepiece_model))
                    return _sentencepiece_tokenizer(sp_tokenizer)
                except Exception:
                    pass
    return _fallback_surface_tokenizer()
def _evaluate_semantic(
    outputs: Sequence[str],
    references: Sequence[str],
    *,
    model_type: str,
    batch_size: int,
    device: str | None = None,
) -> dict[str, float]:
    if not outputs or not references:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    from bert_score import BERTScorer

    resolved_device = device or _detect_torch_device()
    scorer = BERTScorer(
        model_type=model_type,
        batch_size=batch_size,
        device=resolved_device,
        rescale_with_baseline=True,
    )
    precisions, recalls, f1s = scorer.score(outputs, references)
    return {
        "precision": round(_mean(precisions), 4),
        "recall": round(_mean(recalls), 4),
        "f1": round(_mean(f1s), 4),
    }


def _evaluate_surface(
    outputs: Sequence[str],
    references: Sequence[str],
    *,
    sentencepiece_model: Path | None,
) -> dict[str, float]:
    if not outputs or not references:
        return {"rouge1": 0.0, "rougeL": 0.0}
    from rouge_score import rouge_scorer

    tokenizer = _build_surface_tokenizer(sentencepiece_model)
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False, tokenizer=tokenizer)
    rouge1_scores: list[float] = []
    rougeL_scores: list[float] = []
    for output, reference in zip(outputs, references):
        result = scorer.score(reference, output)
        rouge1_scores.append(float(result["rouge1"].fmeasure))
        rougeL_scores.append(float(result["rougeL"].fmeasure))
    return {
        "rouge1": round(_mean(rouge1_scores), 4),
        "rougeL": round(_mean(rougeL_scores), 4),
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
    gathering_contains: str | None = None
    lines = text.splitlines()
    idx = 0

    def _consume_block_scalar(
        start_idx: int, indent_level: int, indicator: str
    ) -> tuple[str, int]:
        indicator_token: list[str] = []
        for char in indicator:
            if char in {" ", "\t", "#"}:
                break
            indicator_token.append(char)
        if not indicator_token:
            indicator_token.append(indicator[0])

        style = indicator_token[0]
        chomp = "clip"
        for char in indicator_token[1:]:
            if char == "+":
                chomp = "keep"
            elif char == "-":
                chomp = "strip"

        block_lines: list[tuple[str, int | None]] = []
        cursor = start_idx
        while cursor < len(lines):
            candidate_raw = lines[cursor]
            candidate_indent = len(candidate_raw) - len(candidate_raw.lstrip(" "))
            candidate_stripped = candidate_raw.strip()
            if candidate_stripped == "":
                block_lines.append(("", None))
                cursor += 1
                continue
            if candidate_indent <= indent_level:
                break
            block_lines.append((candidate_raw, candidate_indent))
            cursor += 1

        normalized: list[tuple[str, bool]] = []
        if block_lines:
            indents = [indent for _, indent in block_lines if indent is not None]
            trim_indent = min(indents) if indents else indent_level + 1
            for line, indent in block_lines:
                if indent is None:
                    normalized.append(("", False))
                    continue
                start = trim_indent if len(line) >= trim_indent else len(line)
                text = line[start:]
                relative_indent = max(indent - trim_indent, 0)
                normalized.append((text, relative_indent > 0))

        if style == "|":
            value = "".join(f"{text}\n" for text, _ in normalized)
        else:
            folded_lines: list[str] = []
            current_parts: list[str] = []
            pending_blank_lines = 0
            for part, is_deeper_indent in normalized:
                stripped_part = part.strip()
                if not stripped_part:
                    if current_parts:
                        folded_lines.append(" ".join(current_parts))
                        current_parts = []
                    pending_blank_lines += 1
                    continue
                if is_deeper_indent:
                    if current_parts:
                        folded_lines.append(" ".join(current_parts))
                        current_parts = []
                    if pending_blank_lines:
                        folded_lines.extend([""] * pending_blank_lines)
                        pending_blank_lines = 0
                    folded_lines.append(part)
                    continue
                if pending_blank_lines:
                    folded_lines.extend([""] * pending_blank_lines)
                    pending_blank_lines = 0
                current_parts.append(stripped_part)
            if current_parts:
                folded_lines.append(" ".join(current_parts))
            value = "\n".join(folded_lines)

        has_any_lines = bool(block_lines)
        if chomp == "strip":
            value = value.rstrip("\n")
        elif chomp == "clip":
            if has_any_lines:
                value = value.rstrip("\n") + "\n"
        elif chomp == "keep":
            if has_any_lines and not value.endswith("\n"):
                value = value + "\n"

        return value, cursor

    def _maybe_consume_block_scalar(
        start_idx: int, line: str, value_part: str
    ) -> tuple[str | None, int]:
        payload = value_part.strip()
        if payload and payload[0] in {"|", ">"}:
            indent_level = len(line) - len(line.lstrip(" "))
            value, cursor = _consume_block_scalar(start_idx + 1, indent_level, payload)
            return value, cursor
        return None, start_idx

    def _parse_mapping_block(start_idx: int, base_indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        cursor = start_idx
        while cursor < len(lines):
            candidate_raw = lines[cursor]
            stripped_candidate = candidate_raw.strip()
            if not stripped_candidate or stripped_candidate.startswith("#"):
                cursor += 1
                continue
            indent = len(candidate_raw) - len(candidate_raw.lstrip(" "))
            if indent <= base_indent:
                break
            if ":" not in stripped_candidate:
                cursor += 1
                continue
            key_part, value_part = stripped_candidate.split(":", 1)
            normalized_key = _normalize_yaml_scalar(key_part)
            block_value, new_cursor = _maybe_consume_block_scalar(cursor, candidate_raw, value_part)
            if block_value is not None:
                mapping[normalized_key] = block_value
                cursor = new_cursor
                continue
            payload = value_part.strip()
            if not payload:
                nested, cursor = _parse_mapping_block(cursor + 1, indent)
                mapping[normalized_key] = nested
                continue
            inline_mapping = _parse_loose_mapping(payload)
            if inline_mapping:
                mapping[normalized_key] = inline_mapping
                cursor += 1
                continue
            mapping[normalized_key] = _normalize_yaml_scalar(value_part)
            cursor += 1
        return mapping, cursor

    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped in {"rules", "rules:"}:
            idx += 1
            continue
        if stripped.startswith("- id:"):
            if current:
                rules.append(current)
            current = {
                "id": _normalize_yaml_scalar(stripped.split(":", 1)[1]),
                "match": {},
            }
            gathering_contains = None
            idx += 1
            continue
        if current is None:
            idx += 1
            continue
        if stripped.startswith("description:"):
            value_part = stripped.split(":", 1)[1]
            block_value, new_idx = _maybe_consume_block_scalar(idx, raw, value_part)
            if block_value is not None:
                current["description"] = block_value
                idx = new_idx
                continue
            current["description"] = _normalize_yaml_scalar(value_part)
        elif stripped.startswith("severity:"):
            value_part = stripped.split(":", 1)[1]
            payload = value_part.strip()
            if payload and payload[0] in {"|", ">"}:
                indent_level = len(raw) - len(raw.lstrip(" "))
                value, idx = _consume_block_scalar(idx + 1, indent_level, payload)
                current["severity"] = value
                continue
            current["severity"] = _normalize_yaml_scalar(value_part)
        elif stripped.startswith("when:"):
            value_part = stripped.split(":", 1)[1]
            payload = value_part.strip()
            if payload:
                inline = _parse_loose_mapping(payload)
                if inline:
                    current["when"] = inline
                    idx += 1
                    continue
            indent_level = len(raw) - len(raw.lstrip(" "))
            mapping, idx = _parse_mapping_block(idx + 1, indent_level)
            current["when"] = mapping
            continue
        elif stripped.startswith("any:"):
            match = current.setdefault("match", {})
            match.setdefault("any", [])
            gathering_contains = "any"
            idx += 1
            continue
        elif stripped.startswith("all:"):
            match = current.setdefault("match", {})
            match.setdefault("all", [])
            gathering_contains = "all"
            idx += 1
            continue
        elif stripped.startswith("- contains:") and gathering_contains:
            value_part = stripped.split(":", 1)[1]
            payload = value_part.strip()
            indent_level = len(raw) - len(raw.lstrip(" "))
            if payload and payload[0] in {"|", ">"}:
                value, idx = _consume_block_scalar(idx + 1, indent_level, payload)
                match = current.setdefault("match", {})
                match.setdefault(gathering_contains, []).append({"contains": value})
                continue
            # コメント除去とクオート除去を事前処理しつつ、正規化関数に委譲
            is_quoted = len(payload) >= 2 and payload[0] == payload[-1] and payload[0] in {'"', "'"}
            if not is_quoted:
                comment_index = payload.find("#")
                if comment_index != -1:
                    payload = payload[:comment_index].rstrip()

            payload = _normalize_yaml_scalar(payload)

            match = current.setdefault("match", {})
            match.setdefault(gathering_contains, []).append({"contains": payload})
            idx += 1
            continue
        elif not raw.startswith("  "):
            gathering_contains = None
        idx += 1
    if current:
        rules.append(current)
    return {"rules": rules}


def _value_matches(expected: Any, actual: Any) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            return False
        return _matches_mapping(expected, actual)
    if isinstance(expected, (list, tuple, set)):
        return any(_value_matches(option, actual) for option in expected)
    if expected is None:
        return actual is None
    if actual is None:
        return False
    if actual == expected:
        return True
    return str(actual) == str(expected)


def _matches_mapping(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> bool:
    actual_with_str_keys = {str(key): value for key, value in actual.items()}
    for key, expected_value in expected.items():
        key_str = str(key)
        if key_str not in actual_with_str_keys:
            return False
        actual_value = actual_with_str_keys[key_str]
        if not _value_matches(expected_value, actual_value):
            return False
    return True


def _evaluate_when(conditions: Any, item: EvaluationItem) -> bool:
    if not conditions:
        return True
    if not isinstance(conditions, dict):
        return True
    metadata_conditions = conditions.get("metadata")
    if metadata_conditions is not None:
        if not isinstance(metadata_conditions, Mapping):
            return False
        if not _matches_mapping(metadata_conditions, item.metadata):
            return False
    return True


def _matches_rule(rule: dict[str, Any], item: EvaluationItem) -> bool:
    if not _evaluate_when(rule.get("when"), item):
        return False

    text = item.output
    match_section = rule.get("match", {})
    any_nodes: Sequence[Any] | None = None
    all_nodes: Sequence[Any] | None = None

    if isinstance(match_section, dict):
        any_nodes = match_section.get("any")
        all_nodes = match_section.get("all")
    else:
        normalized = str(match_section).strip().lower()
        if normalized == "any":
            any_nodes = rule.get("any")
        elif normalized == "all":
            all_nodes = rule.get("all")

    if any_nodes is None:
        fallback_any = rule.get("any")
        if isinstance(fallback_any, list):
            any_nodes = fallback_any
    if all_nodes is None:
        fallback_all = rule.get("all")
        if isinstance(fallback_all, list):
            all_nodes = fallback_all

    def _extract_contains(nodes: Sequence[Any] | None) -> list[str]:
        values: list[str] = []
        if not nodes:
            return values
        for node in nodes:
            if not isinstance(node, dict):
                continue
            candidate = node.get("contains")
            if isinstance(candidate, str):
                values.append(candidate)
        return values

    any_values = _extract_contains(any_nodes)
    all_values = _extract_contains(all_nodes)

    def _contains_value(candidate: str) -> bool:
        if not candidate:
            return False
        if candidate in text:
            return True
        if candidate.endswith("\n"):
            trimmed = candidate.rstrip("\n")
            if trimmed and trimmed in text:
                return True
        return False

    any_matched = any(_contains_value(value) for value in any_values)
    all_matched = bool(all_values) and all(_contains_value(value) for value in all_values)

    return any_matched or all_matched


def _evaluate_guardrails(ruleset_path: Path, items: Sequence[EvaluationItem]) -> dict[str, Any]:
    counts = {severity: 0 for severity in _SEVERITY_PRIORITY}
    if not items:
        return {"counts": counts, "violations": [], "max_severity": "none"}

    loaded = _load_ruleset(ruleset_path)
    violations: list[dict[str, Any]] = []
    for rule in loaded.get("rules", []):
        severity = str(rule.get("severity", "")).strip().lower()
        if severity not in counts:
            continue
        if any(_matches_rule(rule, item) for item in items):
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
    bert_score: dict[str, Any],
    surface_metrics: dict[str, Any],
    violations: dict[str, Any],
    *,
    generated_at: str | None = None,
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
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    bundle = Path(args.bundle) if args.bundle else None

    inputs_path = _resolve_path(args.inputs, bundle, "inputs.jsonl")
    expected_path = _resolve_path(args.expected, bundle, "expected.jsonl")
    output_path = _resolve_path(args.output, bundle, "metrics.json", allow_missing=True)
    if not inputs_path or not expected_path or not output_path:
        raise SystemExit("inputs, expected, output を指定してください")

    items = _collect_pairs(inputs_path, expected_path)
    outputs = _extract_outputs(items)
    references = _extract_references(items)
    bert_score = _evaluate_semantic(
        outputs,
        references,
        model_type=args.bert_model,
        batch_size=args.bert_batch_size,
    )
    sentencepiece_model = _resolve_sentencepiece_model_path(
        args.sentencepiece_model,
        bundle,
    )
    surface_metrics = _evaluate_surface(
        outputs,
        references,
        sentencepiece_model=sentencepiece_model,
    )
    bert_score_with_threshold, surface_with_threshold = _apply_thresholds(bert_score, surface_metrics)
    violations = _apply_violation_threshold(
        _evaluate_guardrails(Path(args.ruleset), items)
    )
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()
    summary = _summarize_results(
        bert_score_with_threshold,
        surface_with_threshold,
        violations,
        generated_at=generated_at,
    )

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
