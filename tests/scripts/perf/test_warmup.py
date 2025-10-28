"""Tests for scripts.perf.warmup."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

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

    def fake_warmup(
        url: str,
        payload: bytes | None = None,
        *,
        timeout: float = 5.0,
        method: str | None = None,
    ) -> None:
        call_order.append(("warmup", (url, payload, timeout, method)))

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
        ("warmup", ("https://api.day8.example/warmup", b"{}", 1.5, None)),
    ]


def test_send_warmup_request_sets_json_header(monkeypatch: pytest.MonkeyPatch, warmup_module) -> None:
    call_order: List[Tuple[str, Tuple[object, ...]]] = []
    class DummyRequest:
        def __init__(self, url: str, data: bytes | None, method: str) -> None:
            self.url = url
            self.data = data
            self.method = method
            self.headers: dict[str, str] = {}

        def add_header(self, key: str, value: str) -> None:
            self.headers[key] = value
            call_order.append(("add_header", (key, value)))

    last_request: DummyRequest | None = None

    def fake_request(url: str, data: bytes | None = None, method: str | None = None):
        nonlocal last_request
        if method is None:
            raise AssertionError("method is required")
        req = DummyRequest(url, data, method)
        last_request = req
        call_order.append(("Request", (url, data, method)))
        return req

    class DummyResponse:
        def __enter__(self):
            call_order.append(("enter", ()))
            return self

        def __exit__(self, exc_type, exc, tb):
            call_order.append(("exit", (exc_type, exc, tb)))
            return False

        def read(self) -> None:
            call_order.append(("read", ()))

    def fake_urlopen(req: DummyRequest, timeout: float):
        call_order.append(("urlopen", (req, timeout)))
        return DummyResponse()

    monkeypatch.setattr(warmup_module.request, "Request", fake_request)
    monkeypatch.setattr(warmup_module.request, "urlopen", fake_urlopen)

    warmup_module.send_warmup_request(
        "https://api.day8.example/warmup",
        payload=b"{}",
        timeout=2.0,
    )

    assert last_request is not None
    assert call_order == [
        ("Request", ("https://api.day8.example/warmup", b"{}", "POST")),
        ("add_header", ("Content-Type", "application/json")),
        ("urlopen", (last_request, 2.0)),
        ("enter", ()),
        ("read", ()),
        ("exit", (None, None, None)),
    ]

    assert last_request.headers == {"Content-Type": "application/json"}


def test_send_warmup_request_uses_explicit_method_without_payload(
    monkeypatch: pytest.MonkeyPatch, warmup_module
) -> None:
    captured_method: list[str] = []

    class DummyRequest:
        def __init__(self, url: str, data: bytes | None, method: str) -> None:
            captured_method.append(method)

    def fake_request(url: str, data: bytes | None = None, method: str | None = None):
        if method is None:
            raise AssertionError("method is required")
        return DummyRequest(url, data, method)

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> None:  # pragma: no cover - no behaviour under test
            pass

    def fake_urlopen(req, timeout: float):
        return DummyResponse()

    monkeypatch.setattr(warmup_module.request, "Request", fake_request)
    monkeypatch.setattr(warmup_module.request, "urlopen", fake_urlopen)

    warmup_module.send_warmup_request(
        "https://api.day8.example/warmup",
        payload=None,
        timeout=1.0,
        method="POST",
    )

    assert captured_method == ["POST"]


def test_warmup_forwards_method_to_send_warmup_request(
    monkeypatch: pytest.MonkeyPatch, warmup_module
) -> None:
    recorded_calls: list[tuple[str, tuple[object, ...]]] = []

    def fake_health(url: str, timeout: float = 5.0) -> None:
        recorded_calls.append(("health", (url, timeout)))

    def fake_send(
        url: str,
        payload: bytes | None = None,
        *,
        timeout: float = 5.0,
        method: str | None = None,
    ) -> None:
        recorded_calls.append(("warmup", (url, payload, timeout, method)))

    monkeypatch.setattr(warmup_module, "perform_health_check", fake_health)
    monkeypatch.setattr(warmup_module, "send_warmup_request", fake_send)

    warmup_module.warmup(
        "https://api.day8.example/healthz",
        "https://api.day8.example/warmup",
        timeout=2.5,
        method="PATCH",
    )

    assert recorded_calls == [
        ("health", ("https://api.day8.example/healthz", 2.5)),
        ("warmup", ("https://api.day8.example/warmup", None, 2.5, "PATCH")),
    ]
