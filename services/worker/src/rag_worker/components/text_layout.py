from typing import Any


def assign_spans(elements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Build parse full_text and char spans (contracts/artifacts/parse.schema.json description):
    full_text = texts of elements that are non-empty and not page_header/page_footer, joined with
    '\\n\\n'; each such element gets char_start/char_end (exclusive) into full_text; the others get
    None/None. Returns (new element dicts, full_text); input not mutated."""
    raise NotImplementedError("not implemented")
