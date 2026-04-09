"""Tests for text normalization."""

from app.extraction.normalizer import normalize_text, add_page_boundaries


def test_normalize_collapses_whitespace():
    text = "hello    world   here"
    assert normalize_text(text) == "hello world here"


def test_normalize_preserves_newlines():
    text = "line one\nline two"
    result = normalize_text(text)
    assert "line one\nline two" in result


def test_normalize_collapses_excessive_newlines():
    text = "a\n\n\n\n\nb"
    result = normalize_text(text)
    assert result == "a\n\nb"


def test_normalize_strips_null_bytes():
    text = "hello\x00world"
    assert normalize_text(text) == "helloworld"


def test_normalize_replaces_smart_quotes():
    text = "\u201cHello\u201d \u2018world\u2019"
    result = normalize_text(text)
    assert '"Hello" \'world\'' == result


def test_normalize_empty():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""


def test_add_page_boundaries():
    pages = ["Page one content", "Page two content"]
    result = add_page_boundaries(pages)
    assert "--- PAGE 1 ---" in result
    assert "--- PAGE 2 ---" in result
    assert "Page one content" in result
    assert "Page two content" in result
