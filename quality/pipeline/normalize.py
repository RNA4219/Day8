"""テキスト正規化ユーティリティ."""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from typing import Sequence, TextIO

from bs4 import BeautifulSoup

_NEWLINE_PATTERN = re.compile(r"\r\n?|\n")
_CODE_FENCE_PATTERN = re.compile(r"```(?:[\w+-]+\n)?(.*?)```", re.DOTALL)
_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_BOLD_PATTERN = re.compile(r"(\*\*|__)(.*?)\1")
_ITALIC_PATTERN = re.compile(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)|_([^_]+?)_")
_STRIKE_PATTERN = re.compile(r"~~(.*?)~~")
_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\([^\)]+\)")
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
_HEADING_PATTERN = re.compile(r"^\s{0,3}#+\s*", re.MULTILINE)
_BLOCKQUOTE_PATTERN = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_MULTI_BLANK_PATTERN = re.compile(r"\n{3,}")
_TRAILING_WS_PATTERN = re.compile(r"[ \t]+\n")
def _sanitize_html(text: str) -> str:
    if "<" not in text or ">" not in text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    extracted = soup.get_text("\n").replace("\xa0", " ")
    return extracted.strip()


def _strip_markdown(text: str) -> str:
    def _replace_code_fence(match: re.Match[str]) -> str:
        content = match.group(1)
        if content is None:
            return ""
        return content.strip("\n")

    cleaned = _CODE_FENCE_PATTERN.sub(_replace_code_fence, text)
    cleaned = _INLINE_CODE_PATTERN.sub(lambda m: m.group(1), cleaned)
    cleaned = _BOLD_PATTERN.sub(lambda m: m.group(2), cleaned)
    cleaned = _ITALIC_PATTERN.sub(lambda m: m.group(1) or m.group(2) or "", cleaned)
    cleaned = _STRIKE_PATTERN.sub(lambda m: m.group(1), cleaned)
    cleaned = _IMAGE_PATTERN.sub(lambda m: m.group(1), cleaned)
    cleaned = _LINK_PATTERN.sub(lambda m: m.group(1), cleaned)
    cleaned = _HEADING_PATTERN.sub("", cleaned)
    cleaned = _BLOCKQUOTE_PATTERN.sub("", cleaned)
    return cleaned


def normalize(text: str) -> str:
    """Appendix E が想定する正規化を実行する."""

    staged = _NEWLINE_PATTERN.sub("\n", unescape(text))
    staged = staged.replace("\u3000", " ")
    staged = _sanitize_html(staged)
    staged = _strip_markdown(staged)
    staged = staged.replace("\u3000", " ")
    staged = _TRAILING_WS_PATTERN.sub("\n", staged)
    staged = _MULTI_BLANK_PATTERN.sub("\n\n", staged)
    trailing_newline = staged.endswith("\n")
    result = staged.strip()
    if not result:
        return result
    if trailing_newline and not result.endswith("\n"):
        result = f"{result}\n"
    return result


def normalize_stream(reader: TextIO, writer: TextIO) -> None:
    writer.write(normalize(reader.read()))


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize text for quality evaluation")
    parser.add_argument("-i", "--input", type=str, help="入力ファイル (省略時は stdin)")
    parser.add_argument("-o", "--output", type=str, help="出力ファイル (省略時は stdout)")
    args = parser.parse_args(argv)

    if args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            content = handle.read()
    else:
        content = sys.stdin.read()

    result = normalize(content)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result)
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli())
