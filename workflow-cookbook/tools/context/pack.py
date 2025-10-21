from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from ppr import personalize_scores


@dataclass(frozen=True)
class Config:
    lam: float
    theta: float
    weights: Mapping[str, float]
    halflife: int
    mu_file: float
    mu_role: float
    limit_candidates: int
    iters: int
    tol: float


def _parse_scalar(value: str) -> float | int:
    try:
        if value.lower() in {"true", "false"}:
            return 1 if value.lower() == "true" else 0
        if any(char in value for char in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return float(value) if value else 0.0


def _load_config(path: Path) -> Config:
    text = path.read_text(encoding="utf-8")
    payload: dict[str, dict[str, float]] = {}
    stack: list[tuple[int, dict[str, object]]] = []
    current: dict[str, object] = payload
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        while stack and indent <= stack[-1][0]:
            _, current = stack.pop()
        key, _, remainder = raw_line.strip().partition(":")
        if not _:
            continue
        value = remainder.strip()
        if not value:
            next_map: dict[str, object] = {}
            current[key] = next_map
            stack.append((indent, current))
            current = next_map
        else:
            current[key] = _parse_scalar(value)
    pagerank = payload.get("pagerank", {})
    weights = payload.get("weights", {})
    diversity = payload.get("diversity", {})
    limits = payload.get("limits", {})
    return Config(
        lam=float(pagerank.get("lambda", 0.85)),
        theta=float(pagerank.get("theta", 0.6)),
        weights={
            "intent": float(weights.get("intent", 0.4)),
            "diff": float(weights.get("diff", 0.25)),
            "recency": float(weights.get("recency", 0.2)),
            "hub": float(weights.get("hub", 0.1)),
            "role": float(weights.get("role", 0.05)),
        },
        halflife=int(payload.get("recency_halflife_days", 45)),
        mu_file=float(diversity.get("mu_file", 0.15)),
        mu_role=float(diversity.get("mu_role", 0.1)),
        limit_candidates=int(limits.get("ncand", 2000)),
        iters=int(limits.get("iters", 50)),
        tol=float(limits.get("tol", 1e-6)),
    )


def _tokenize(text: str) -> set[str]:
    return {part for part in re.findall(r"[a-z0-9]+", text.lower()) if part}


def _intent_profile(intent: str) -> dict[str, object]:
    tokens = _tokenize(intent)
    role = None
    for candidate in ("impl", "ops", "spec", "risk"):
        if candidate in tokens:
            role = candidate
            break
    return {"raw": intent, "keywords": tokens, "role": role}


def _intent_match(tokens: set[str], node: Mapping[str, object]) -> float:
    node_tokens = _tokenize(str(node.get("heading", "")) + " " + str(node.get("path", "")))
    if not tokens and not node_tokens:
        return 0.0
    if not tokens:
        return 0.0
    intersection = len(tokens & node_tokens)
    if intersection == 0:
        return 0.0
    union = len(tokens | node_tokens)
    return intersection / union


def _diff_score(path: str, node_role: str | None, intent_role: str | None, diff_paths: set[str]) -> float:
    if not path:
        return 0.0
    if path in diff_paths:
        return 1.0
    parents = {str(Path(item).parent) for item in diff_paths}
    for parent in parents:
        if parent and str(path).startswith(parent):
            return 0.7
    if intent_role and node_role and intent_role == node_role:
        return 0.4
    return 0.0


def _recency_score(timestamp: str, halflife: int) -> float:
    if not timestamp:
        return 0.0
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    age = (datetime.now(timezone.utc) - parsed).total_seconds() / 86400
    return math.exp(-max(age, 0.0) / max(halflife, 1))


def _hub_scores(nodes: list[Mapping[str, object]], edges: Iterable[Mapping[str, object]]) -> dict[str, float]:
    outdeg: dict[str, int] = {str(node["id"]): 0 for node in nodes}
    for edge in edges:
        src = str(edge.get("src", ""))
        if src in outdeg:
            outdeg[src] += 1
    max_deg = max(outdeg.values(), default=0)
    denom = math.log1p(max_deg) if max_deg else 1.0
    return {node_id: (math.log1p(deg) / denom if denom else 0.0) for node_id, deg in outdeg.items()}


def _base_signals(
    node: Mapping[str, object],
    profile: Mapping[str, object],
    diff_paths: set[str],
    hub_scores: Mapping[str, float],
    cfg: Config,
) -> dict[str, float]:
    node_role = str(node.get("role") or "") or None
    intent_role = profile.get("role") if isinstance(profile.get("role"), str) else None
    intent_hit = _intent_match(profile.get("keywords", set()), node)
    diff_hit = _diff_score(str(node.get("path", "")), node_role, intent_role, diff_paths)
    recency = _recency_score(str(node.get("mtime", "")), cfg.halflife)
    hub = hub_scores.get(str(node.get("id", "")), 0.0)
    if intent_role and node_role == intent_role:
        role = 0.6
    elif intent_role and node_role and node_role != intent_role:
        role = 0.2
    else:
        role = 0.4
    return {
        "intent": intent_hit,
        "diff": diff_hit,
        "recency": recency,
        "hub": hub,
        "role": role,
    }


def _combine_score(signals: Mapping[str, float], weights: Mapping[str, float]) -> float:
    return sum(float(signals.get(key, 0.0)) * float(weights.get(key, 0.0)) for key in weights)


def _candidate_neighbourhood(
    nodes: list[Mapping[str, object]],
    edges: Iterable[Mapping[str, object]],
    seeds: set[str],
    hops: int = 2,
) -> set[str]:
    adjacency: dict[str, set[str]] = {str(node["id"]): set() for node in nodes}
    for edge in edges:
        src = str(edge.get("src", ""))
        dst = str(edge.get("dst", ""))
        if src in adjacency and dst in adjacency:
            adjacency[src].add(dst)
            adjacency[dst].add(src)
    visited = set(seeds)
    queue = deque((seed, 0) for seed in seeds)
    while queue:
        current, depth = queue.popleft()
        if depth >= hops:
            continue
        for neighbour in adjacency.get(current, set()):
            if neighbour in visited:
                continue
            visited.add(neighbour)
            queue.append((neighbour, depth + 1))
    return visited


def _parse_budget(raw: str) -> int:
    cleaned = raw.strip().lower()
    if cleaned.endswith("k"):
        return int(float(cleaned[:-1]) * 1000)
    return int(cleaned)


def _load_graph(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _token_count(node: Mapping[str, object]) -> int:
    for key in ("tok", "tokens", "token_count"):
        value = node.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def generate_pack(args: argparse.Namespace) -> dict[str, object]:
    graph_path = Path(args.graph)
    output_path = Path(args.output)
    config_path = Path(args.config)
    if isinstance(args.budget, str):
        args.budget = _parse_budget(args.budget)
    cfg = _load_config(config_path)
    graph = _load_graph(graph_path)
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))
    profile = _intent_profile(args.intent)
    diff_paths = {str(item) for item in getattr(args, "diff", [])}
    hub_scores = _hub_scores(nodes, edges)

    signals: dict[str, dict[str, float]] = {}
    base_scores: dict[str, float] = {}
    for node in nodes:
        node_id = str(node.get("id", ""))
        node_signals = _base_signals(node, profile, diff_paths, hub_scores, cfg)
        signals[node_id] = node_signals
        base_scores[node_id] = _combine_score(node_signals, cfg.weights)

    if args.ppr:
        ppr_scores = personalize_scores(nodes, edges, base_scores, cfg.lam, cfg.iters, cfg.tol)
    else:
        ppr_scores = {node_id: base_scores[node_id] for node_id in base_scores}

    scores: dict[str, float] = {}
    for node_id, base_value in base_scores.items():
        ppr_value = ppr_scores.get(node_id, 0.0)
        scores[node_id] = cfg.theta * ppr_value + (1 - cfg.theta) * base_value

    seeds = {node_id for node_id, sig in signals.items() if sig["intent"] > 0 or sig["diff"] > 0}
    candidate_ids = (
        _candidate_neighbourhood(nodes, edges, seeds)
        if seeds
        else {str(node.get("id", "")) for node in nodes}
    )
    scored_candidates = sorted(candidate_ids, key=lambda node_id: scores.get(node_id, 0.0), reverse=True)
    scored_candidates = scored_candidates[: cfg.limit_candidates]

    selections: list[dict[str, object]] = []
    token_in = 0
    diversity_penalty = 0.0
    file_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    total_tokens = sum(_token_count(node) for node in nodes)
    for node_id in scored_candidates:
        node = next((item for item in nodes if str(item.get("id")) == node_id), None)
        if not node:
            continue
        tokens = _token_count(node)
        prospective = token_in + tokens
        if prospective > args.budget:
            continue
        path = str(node.get("path", ""))
        role = str(node.get("role", "")) if node.get("role") else ""
        selected_count = len(selections)
        file_ratio = file_counts.get(path, 0) / (selected_count + 1 or 1)
        role_ratio = role_counts.get(role, 0) / (selected_count + 1 or 1)
        penalty_factor = 1 - (cfg.mu_file * file_ratio + cfg.mu_role * role_ratio)
        adjusted_score = scores.get(node_id, 0.0) * max(penalty_factor, 0.0)
        diversity_penalty += max(scores.get(node_id, 0.0) - adjusted_score, 0.0)
        if adjusted_score <= 0.0:
            continue
        token_in = prospective
        file_counts[path] = file_counts.get(path, 0) + 1
        role_counts[role] = role_counts.get(role, 0) + 1
        why = dict(signals[node_id])
        why["ppr"] = ppr_scores.get(node_id, 0.0)
        selections.append(
            {
                "id": node_id,
                "tok": tokens,
                "filters": ["lossless", "pointer", "role_extract"],
                "why": why,
            }
        )
        if token_in >= args.budget:
            break

    dup_rate = 0.0
    if selections:
        paths = [next((node for node in nodes if str(node.get("id")) == section["id"]), {}).get("path") for section in selections]
        unique_paths = {path for path in paths if path}
        dup_rate = 1 - (len(unique_paths) / len(paths)) if paths else 0.0

    entropy = 0.0
    if ppr_scores:
        norm = sum(ppr_scores.values()) or 1.0
        for value in ppr_scores.values():
            prob = value / norm if norm else 0.0
            if prob > 0:
                entropy -= prob * math.log(prob)

    pack = {
        "intent": args.intent,
        "budget": str(args.budget),
        "sections": selections,
        "metrics": {
            "token_in": token_in,
            "token_src": total_tokens,
            "dup_rate": dup_rate,
            "ppr_entropy": entropy,
            "diversity_penalty": diversity_penalty,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return pack


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate context packs with PPR scoring")
    parser.add_argument("--graph", default="reports/context/graph.json")
    parser.add_argument("--output", default="reports/context/pack.json")
    default_config = Path(__file__).with_name("config.yaml")
    parser.add_argument("--config", default=str(default_config))
    parser.add_argument("--intent", required=True)
    parser.add_argument("--budget", required=True)
    parser.add_argument("--ppr", action="store_true")
    parser.add_argument("--diff", nargs="*", default=[])
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(argv)
    parsed.budget = _parse_budget(str(parsed.budget))
    generate_pack(parsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
