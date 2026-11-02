"""Unit tests for text_layout.assign_spans (full_text + char spans): build inputs inline, call the
function directly, assert exact dicts."""

from copy import deepcopy
from typing import Any

from rag_worker.components.text_layout import assign_spans


def _element(eid: str, type: str, text: str) -> dict[str, Any]:
    return {
        "id": eid,
        "type": type,
        "text": text,
        "char_start": None,
        "char_end": None,
    }


def _spans(elements: list[dict[str, Any]]) -> dict[str, tuple[Any, Any]]:
    return {e["id"]: (e["char_start"], e["char_end"]) for e in elements}


def test_full_text_and_spans_for_two_texts() -> None:
    out, full_text = assign_spans(
        [_element("e-0000", "text", "A"), _element("e-0001", "text", "B")]
    )
    assert full_text == "A\n\nB"
    assert _spans(out) == {"e-0000": (0, 1), "e-0001": (3, 4)}


def test_header_footer_and_empty_get_none_spans_and_are_not_in_full_text() -> None:
    elements = [
        _element("e-0000", "page_header", "Header"),
        _element("e-0001", "text", "Body"),
        _element("e-0002", "text", ""),
        _element("e-0003", "page_footer", "Page 1"),
        _element("e-0004", "text", "More"),
    ]
    out, full_text = assign_spans(elements)
    assert full_text == "Body\n\nMore"
    assert _spans(out) == {
        "e-0000": (None, None),
        "e-0001": (0, 4),
        "e-0002": (None, None),
        "e-0003": (None, None),
        "e-0004": (6, 10),
    }


def test_input_list_not_mutated() -> None:
    elements = [
        _element("e-0000", "page_header", "Header"),
        _element("e-0001", "text", "A"),
        _element("e-0002", "text", "B"),
    ]
    original = deepcopy(elements)
    out, full_text = assign_spans(elements)
    assert elements == original
    assert full_text == "A\n\nB"
    assert _spans(out) == {"e-0000": (None, None), "e-0001": (0, 1), "e-0002": (3, 4)}


def test_unicode_span_length_counts_characters() -> None:
    out, full_text = assign_spans([_element("e-0000", "text", "čaj")])
    assert full_text == "čaj"
    start, end = _spans(out)["e-0000"]
    assert end - start == 3
    assert full_text[start:end] == "čaj"


def test_empty_elements_list_gives_empty_full_text() -> None:
    out, full_text = assign_spans([])
    assert out == []
    assert full_text == ""
