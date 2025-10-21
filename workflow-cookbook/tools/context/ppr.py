from __future__ import annotations

from typing import Iterable, Mapping


def personalize_scores(
    nodes: Iterable[Mapping[str, object]],
    edges: Iterable[Mapping[str, object]],
    base_scores: Mapping[str, float],
    lam: float = 0.85,
    iters: int = 50,
    tol: float = 1e-6,
) -> dict[str, float]:
    indexed_nodes = list(nodes)
    size = len(indexed_nodes)
    if size == 0:
        return {}
    id_to_index = {str(node["id"]): idx for idx, node in enumerate(indexed_nodes)}
    adjacency: list[list[int]] = [[] for _ in range(size)]
    outdeg = [0] * size
    for edge in edges:
        src = id_to_index.get(str(edge.get("src", "")))
        dst = id_to_index.get(str(edge.get("dst", "")))
        if src is None or dst is None:
            continue
        adjacency[src].append(dst)
        outdeg[src] += 1

    seed = [max(float(base_scores.get(str(node["id"]), 0.0)), 0.0) for node in indexed_nodes]
    total = sum(seed)
    if total == 0.0:
        seed = [1.0 / size] * size
    else:
        seed = [value / total for value in seed]

    ranks = [1.0 / size] * size
    for _ in range(max(iters, 1)):
        next_ranks = [(1 - lam) * seed[idx] for idx in range(size)]
        dangling_mass = sum(ranks[idx] for idx, deg in enumerate(outdeg) if deg == 0)
        if dangling_mass:
            share = lam * dangling_mass / size
            for idx in range(size):
                next_ranks[idx] += share
        for src, deg in enumerate(outdeg):
            if deg == 0:
                continue
            weight = lam * ranks[src] / deg
            for dst in adjacency[src]:
                next_ranks[dst] += weight
        delta = sum(abs(next_ranks[idx] - ranks[idx]) for idx in range(size))
        ranks = next_ranks
        if delta < tol:
            break

    normaliser = sum(ranks) or 1.0
    return {str(indexed_nodes[idx]["id"]): ranks[idx] / normaliser for idx in range(size)}
