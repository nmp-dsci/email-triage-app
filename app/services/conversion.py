from __future__ import annotations

import mimetypes
from html.parser import HTMLParser
from pathlib import Path

try:
    from markitdown import MarkItDown
except Exception:  # pragma: no cover - dependency may be absent in light test envs
    MarkItDown = None  # type: ignore[assignment]


class ConversionError(RuntimeError):
    pass


def convert_to_markdown(path: Path, content_type: str | None = None) -> str:
    try:
        if MarkItDown is None:
            raise RuntimeError("markitdown is not installed")
        converted = MarkItDown().convert(str(path))
        text = getattr(converted, "text_content", None) or str(converted)
        return text.strip()
    except Exception as exc:
        fallback = _fallback_convert(path, content_type)
        if fallback:
            return fallback
        raise ConversionError(f"Failed to convert {path.name}: {exc}") from exc


def _fallback_convert(path: Path, content_type: str | None) -> str:
    guessed = content_type or mimetypes.guess_type(path.name)[0] or ""
    if guessed.startswith("text/") or path.suffix.lower() in {".md", ".txt", ".csv"}:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    if guessed == "text/html" or path.suffix.lower() in {".html", ".htm"}:
        return html_to_text(path.read_text(encoding="utf-8", errors="replace")).strip()
    return ""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "br", "li", "tr", "div"}:
            self.parts.append("\n")


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(part for part in parser.parts if part).replace(" \n ", "\n")
