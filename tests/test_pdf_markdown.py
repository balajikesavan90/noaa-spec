"""Tests for deterministic PDF to markdown helpers."""

from __future__ import annotations

from noaa_climate_data.pdf_markdown import normalize_extracted_text, render_markdown_document


def test_normalize_extracted_text_is_stable() -> None:
    raw = "  A\u00A0Title\r\n\r\n\r\nLine 1  \r\nLine 2\r\n"
    normalized = normalize_extracted_text(raw)
    assert normalized == "A Title\n\nLine 1\nLine 2"


def test_render_markdown_document_with_page_headers() -> None:
    markdown = render_markdown_document(
        ["First page body", "Second page body"],
        source_name="spec.pdf",
        include_page_headers=True,
    )
    assert markdown.startswith("# spec.pdf\n")
    assert "## Page 1" in markdown
    assert "## Page 2" in markdown
    assert markdown.endswith("\n")


def test_render_markdown_document_without_page_headers() -> None:
    markdown = render_markdown_document(
        ["Only body"],
        source_name="spec.pdf",
        include_page_headers=False,
    )
    assert "## Page" not in markdown
    assert "Only body" in markdown
