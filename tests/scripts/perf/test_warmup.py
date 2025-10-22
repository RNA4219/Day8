"""Tests for scripts.perf.warmup."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import importlib.util
import sys

import pytest


MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "perf" / "warmup.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scripts.perf.warmup", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load warmup module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.perf.warmup", module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def warmup_module():
    return _load_module()


def test_warmup_runs_healthcheck_then_warmup(monkeypatch: pytest.MonkeyPatch, warmup_module) -> None:
    call_order: List[Tuple[str, Tuple[object, ...]]] = []

    def fake_health(url: str, timeout: float = 5.0) -> None:
        call_order.append(("health", (url, timeout)))

    def fake_warmup(url: str, payload: bytes | None = None, timeout: float = 5.0) -> None:
        call_order.append(("warmup", (url, payload, timeout)))

    monkeypatch.setattr(warmup_module, "perform_health_check", fake_health)
    monkeypatch.setattr(warmup_module, "send_warmup_request", fake_warmup)

    warmup_module.warmup(
        "https://api.day8.example/healthz",
        "https://api.day8.example/warmup",
        payload=b"{}",
        timeout=1.5,
    )

    assert call_order == [
        ("health", ("https://api.day8.example/healthz", 1.5)),
        ("warmup", ("https://api.day8.example/warmup", b"{}", 1.5)),
    ]
