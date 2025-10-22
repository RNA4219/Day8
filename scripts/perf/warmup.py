"""Warmup helpers for Day8 API endpoints."""
from __future__ import annotations

from typing import Final
from urllib import request

DEFAULT_TIMEOUT: Final[float] = 5.0


def perform_health_check(url: str, timeout: float = DEFAULT_TIMEOUT) -> None:
    """Execute a GET request against the healthcheck endpoint."""
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as response:  # type: ignore[arg-type]
        response.read()


def send_warmup_request(
    url: str,
    payload: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> None:
    """Send a warmup request, defaulting to GET when no payload is provided."""
    method = "POST" if payload is not None else "GET"
    req = request.Request(url, data=payload, method=method)
    with request.urlopen(req, timeout=timeout) as response:  # type: ignore[arg-type]
        response.read()


def warmup(
    healthcheck_url: str,
    warmup_url: str,
    *,
    payload: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> None:
    """Run the warmup flow: healthcheck first, then warmup request."""
    perform_health_check(healthcheck_url, timeout=timeout)
    send_warmup_request(warmup_url, payload=payload, timeout=timeout)
