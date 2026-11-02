from typing import Any

EXCLUDED_SPAN_TYPES = ("page_header", "page_footer")


def assign_spans(elements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Build parse full_text and char spans (contracts/artifacts/parse.schema.json description):
    full_text = texts of elements that are non-empty and not page_header/page_footer, joined with
    '\\n\\n'; each such element gets char_start/char_end (exclusive) into full_text; the others get
    None/None. Returns (new element dicts, full_text); input not mutated."""
    out: list[dict[str, Any]] = []
    parts: list[str] = []
    start = 0
    for element in elements:
        text = element["text"]
        new_element = dict(element)
        if element["type"] not in EXCLUDED_SPAN_TYPES and text:
            parts.append(text)
            new_element["char_start"] = start
            new_element["char_end"] = start + len(text)
            start += len(text) + 2
        else:
            new_element["char_start"] = None
            new_element["char_end"] = None
        out.append(new_element)
    return out, "\n\n".join(parts)
