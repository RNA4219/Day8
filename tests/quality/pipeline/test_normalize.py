"""quality.pipeline.normalize のユニットテスト."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quality.pipeline.normalize import normalize, normalize_stream


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("line1\r\nline2\rline3\n", "line1\nline2\nline3\n"),
        ("前置\u3000後置", "前置 後置"),
    ],
)
def test_normalize_basic_cleanup(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_normalize_html_sanitization() -> None:
    html = "<div><p>Title</p><script>alert(1)</script><p>Body<br/>Line</p></div>"
    assert normalize(html) == "Title\nBody\nLine"


def test_normalize_markdown_sanitization() -> None:
    markdown_text = (
        "# Heading\n\nSome **bold** text with [link](https://example.com).\n\n"
        "`code` and ![alt](image.png) with ~~strikethrough~~."
    )
    expected = "Heading\n\nSome bold text with link.\n\ncode and alt with strikethrough."
    assert normalize(markdown_text) == expected


def test_normalize_stream_io() -> None:
    source = io.StringIO("<p>Hello&nbsp;World</p>")
    sink = io.StringIO()
    normalize_stream(source, sink)
    assert sink.getvalue() == "Hello World"
