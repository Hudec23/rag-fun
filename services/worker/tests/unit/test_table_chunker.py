"""Unit tests for table_documents / TableChunker: build parse elements inline, call the
function/component directly, and assert exact haystack Documents."""

from haystack import Document

from rag_worker.components.table_chunker import TableChunker, table_documents


def _cell(row: int, col: int, text: str, *, header: bool = False) -> dict:
    return {
        "row": row,
        "col": col,
        "row_span": 1,
        "col_span": 1,
        "text": text,
        "is_header": header,
    }


def _markdown(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _text_element(
    element_id: str,
    text: str,
    char_start: int,
    char_end: int,
    *,
    page_no: int = 1,
    section_path: tuple[str, ...] = (),
) -> dict:
    return {
        "id": element_id,
        "type": "text",
        "text": text,
        "page_no": page_no,
        "bbox": None,
        "heading_level": None,
        "section_path": list(section_path),
        "table": None,
        "from_ocr": False,
        "char_start": char_start,
        "char_end": char_end,
    }


def _table_element(
    *,
    markdown: str,
    cells: list[dict],
    element_id: str = "e-0001",
    char_start: int = 0,
    char_end: int = 0,
    page_no: int = 1,
    section_path: tuple[str, ...] = (),
) -> dict:
    num_rows = max(cell["row"] for cell in cells) + 1
    num_cols = max(cell["col"] for cell in cells) + 1
    return {
        "id": element_id,
        "type": "table",
        "text": markdown,
        "page_no": page_no,
        "bbox": None,
        "heading_level": None,
        "section_path": list(section_path),
        "table": {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "cells": cells,
            "markdown": markdown,
        },
        "from_ocr": False,
        "char_start": char_start,
        "char_end": char_end,
    }


def _run(elements: list[dict], source_text: str) -> list[Document]:
    return TableChunker(False, 50, 0).run(elements=elements, source_text=source_text)["documents"]


def test_table_documents_single_table_without_row_chunks() -> None:
    md = _markdown(["product", "price"], [["Basic", "9"]])
    element = _table_element(
        markdown=md,
        cells=[
            _cell(0, 0, "product", header=True),
            _cell(0, 1, "price", header=True),
            _cell(1, 0, "Basic"),
            _cell(1, 1, "9"),
        ],
        char_end=len(md),
        section_path=("Pricing",),
    )
    [doc] = table_documents([element], False)
    assert doc.content == md
    assert doc.meta["element_type"] == "table"
    assert doc.meta["element_ids"] == ["e-0001"]
    assert doc.meta["page_numbers"] == [1]
    assert doc.meta["section_path"] == ["Pricing"]
    assert doc.meta["split_idx_start"] == 0


def test_table_documents_row_chunks_use_header_labels() -> None:
    md = _markdown(["product", "price"], [["Basic", "9"], ["Pro", "29"]])
    element = _table_element(
        markdown=md,
        cells=[
            _cell(0, 0, "product", header=True),
            _cell(0, 1, "price", header=True),
            _cell(1, 0, "Basic"),
            _cell(1, 1, "9"),
            _cell(2, 0, "Pro"),
            _cell(2, 1, "29"),
        ],
    )
    docs = table_documents([element], True)
    assert [doc.content for doc in docs] == [
        md,
        "product: Basic\nprice: 9",
        "product: Pro\nprice: 29",
    ]
    assert docs[0].meta["element_type"] == "table"
    assert docs[0].meta["element_ids"] == ["e-0001"]
    assert docs[1].meta["no_span"] is True
    assert docs[1].meta["element_type"] == "table"
    assert docs[2].meta["no_span"] is True
    assert docs[2].meta["element_type"] == "table"


def test_table_documents_missing_header_falls_back_to_col_label() -> None:
    md = "| product |  |\n|---|---|\n| Basic | 9 |"
    element = _table_element(
        markdown=md,
        cells=[
            _cell(0, 0, "product", header=True),
            _cell(1, 0, "Basic"),
            _cell(1, 1, "9"),
        ],
    )
    docs = table_documents([element], True)
    assert [doc.content for doc in docs] == [md, "product: Basic\ncol1: 9"]
    assert docs[1].meta["no_span"] is True
    assert docs[1].meta["element_type"] == "table"


def test_run_orders_text_table_and_text_by_position() -> None:
    lead = "A" * 60
    trail = "B" * 10
    md = _markdown(["Q", "Rev"], [["Q3", "12"]])
    source = lead + md + trail
    elements = [
        _text_element("e-0000", lead, 0, len(lead)),
        _table_element(
            markdown=md,
            char_start=len(lead),
            char_end=len(lead) + len(md),
            section_path=("Q3 Report",),
            cells=[
                _cell(0, 0, "Q", header=True),
                _cell(0, 1, "Rev", header=True),
                _cell(1, 0, "Q3"),
                _cell(1, 1, "12"),
            ],
        ),
        _text_element("e-0002", trail, len(lead) + len(md), len(source)),
    ]
    docs = _run(elements, source)
    assert [doc.content for doc in docs] == [lead[:50], lead[50:], md, trail]
    assert docs[0].meta["split_idx_start"] == 0
    assert docs[2].meta["element_type"] == "table"
    assert docs[2].meta["split_idx_start"] == len(lead)
    assert docs[2].meta["element_ids"] == ["e-0001"]
    assert docs[2].meta["page_numbers"] == [1]
    assert docs[2].meta["section_path"] == ["Q3 Report"]
    assert docs[3].meta["split_idx_start"] == len(lead) + len(md)


def test_run_without_tables_produces_only_recursive_text_chunks() -> None:
    first = "A" * 30
    second = "B" * 30
    source = first + second
    elements = [
        _text_element("e-0000", first, 0, len(first)),
        _text_element("e-0001", second, len(first), len(source)),
    ]
    docs = _run(elements, source)
    assert [doc.content for doc in docs] == [source[:50], source[50:]]
    assert all(doc.meta.get("element_type") != "table" for doc in docs)
