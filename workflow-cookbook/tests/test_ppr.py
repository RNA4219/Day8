import importlib.util
from pathlib import Path
import math


_DEF_PPR_PATH = Path(__file__).resolve().parents[1] / "tools" / "context" / "ppr.py"


def _load_ppr_module():
    spec = importlib.util.spec_from_file_location("workflow_context_ppr", _DEF_PPR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load ppr module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_personalize_scores_uniform_seed_when_no_base_scores():
    module = _load_ppr_module()
    personalize_scores = module.personalize_scores

    nodes = [{"id": "a"}, {"id": "b"}]
    edges: list[dict[str, object]] = []
    base_scores: dict[str, float] = {}

    ranks = personalize_scores(nodes, edges, base_scores, lam=0.85, iters=10, tol=1e-9)

    assert math.isclose(ranks["a"], 0.5, rel_tol=1e-9)
    assert math.isclose(ranks["b"], 0.5, rel_tol=1e-9)
    assert math.isclose(sum(ranks.values()), 1.0, rel_tol=1e-9)
