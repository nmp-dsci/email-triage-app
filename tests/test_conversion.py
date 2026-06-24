from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _public_conversion_callable(module: Any):
    for name in (
        "convert_attachment_to_markdown",
        "convert_file_to_markdown",
        "convert_to_markdown",
    ):
        converter = getattr(module, name, None)
        if callable(converter):
            return converter
    pytest.fail(
        "app.services.conversion must expose a public conversion function "
        "(convert_attachment_to_markdown, convert_file_to_markdown, or "
        "convert_to_markdown)."
    )


def _markdown_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    for attr in ("markdown", "text", "content", "markdown_text", "text_content"):
        value = getattr(result, attr, None)
        if isinstance(value, str):
            return value
    pytest.fail(f"Conversion result does not expose markdown text: {result!r}")


def test_conversion_wrapper_uses_markitdown_without_live_conversion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    conversion = pytest.importorskip("app.services.conversion")
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"%PDF-1.4 fake test payload")

    calls: list[Path] = []

    class FakeMarkItDown:
        def convert(self, path: str | Path) -> SimpleNamespace:
            calls.append(Path(path))
            return SimpleNamespace(text_content="# Invoice\n\nPay the deposit.")

    monkeypatch.setitem(sys.modules, "markitdown", SimpleNamespace(MarkItDown=FakeMarkItDown))
    monkeypatch.setattr(conversion, "MarkItDown", FakeMarkItDown, raising=False)

    converter = _public_conversion_callable(conversion)
    markdown = _markdown_text(converter(source))

    assert calls == [source]
    assert markdown == "# Invoice\n\nPay the deposit."
