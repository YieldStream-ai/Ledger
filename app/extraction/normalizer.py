"""Text cleanup and whitespace normalization for extracted PDF text."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Clean up extracted text: fix encoding, normalize whitespace, strip artifacts."""
    if not text:
        return ""

    # Normalize unicode (e.g., ligatures, special dashes)
    text = unicodedata.normalize("NFKD", text)

    # Replace common PDF artifacts
    text = text.replace("\x00", "")  # null bytes
    text = text.replace("\xad", "-")  # soft hyphen
    text = text.replace("\u2013", "-")  # en dash
    text = text.replace("\u2014", "-")  # em dash
    text = text.replace("\u2018", "'")  # left single quote
    text = text.replace("\u2019", "'")  # right single quote
    text = text.replace("\u201c", '"')  # left double quote
    text = text.replace("\u201d", '"')  # right double quote

    # Collapse multiple spaces (but preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    return text.strip()


def add_page_boundaries(pages: list[str]) -> str:
    """Join pages with boundary markers."""
    parts = []
    for i, page in enumerate(pages, 1):
        parts.append(f"--- PAGE {i} ---")
        parts.append(page.strip())
    return "\n\n".join(parts)
