"""Unit tests for DoclingExtractor (parse strategies 'docling_layout' / 'docling_ocr'): build a
DoclingDocument inline, call extract() and the component's run() directly, assert exact element
dicts. DoclingExtractor is a stub — every test here is red until T-worker-015."""

import json

from docling_core.types.doc import (
    BoundingBox,
    DocItemLabel,
    DoclingDocument,
    ProvenanceItem,
    Size,
    TableCell,
    TableData,
)
from haystack import Document

from rag_worker.components.docling_extractor import DoclingExtractor, extract


def _cell(row: int, col: int, text: str, *, header: bool = False) -> TableCell:
    return TableCell(
        start_row_offset_idx=row,
        end_row_offset_idx=row + 1,
        start_col_offset_idx=col,
        end_col_offset_idx=col + 1,
        text=text,
        column_header=header,
    )


def _doc() -> DoclingDocument:
    doc = DoclingDocument(name="report")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_title("Report")
    doc.add_heading("Intro", level=1)
    doc.add_text(label=DocItemLabel.TEXT, text="Hello")
    doc.add_table(
        data=TableData(
            num_rows=2,
            num_cols=2,
            table_cells=[
                _cell(0, 0, "A", header=True),
                _cell(0, 1, "B", header=True),
                _cell(1, 0, "1"),
                _cell(1, 1, "2"),
            ],
        ),
        prov=ProvenanceItem(
            page_no=1,
            bbox=BoundingBox(l=72, t=100, r=300, b=180),
            charspan=(0, 10),
        ),
    )
    return doc


def test_element_types_in_reading_order() -> None:
    out = extract(_doc().model_dump())

    elements = out["elements"]
    assert [e["id"] for e in elements] == ["e-0000", "e-0001", "e-0002", "e-0003"]
    assert [e["type"] for e in elements] == ["title", "heading", "text", "table"]
    assert [e["text"] for e in elements[:3]] == ["Report", "Intro", "Hello"]


def test_heading_levels_and_section_path() -> None:
    out = extract(_doc().model_dump())

    title, heading, text, table = out["elements"]
    assert title["heading_level"] == 1
    assert title["section_path"] == []
    assert heading["heading_level"] == 2
    assert heading["section_path"] == ["Report"]
    assert text["heading_level"] is None
    assert text["section_path"] == ["Report", "Intro"]
    assert table["heading_level"] is None
    assert table["section_path"] == ["Report", "Intro"]


def test_table_element_cells_and_markdown() -> None:
    out = extract(_doc().model_dump())

    [table_element] = [e for e in out["elements"] if e["type"] == "table"]
    table = table_element["table"]
    assert table["num_rows"] == 2
    assert table["num_cols"] == 2
    assert "|" in table["markdown"]
    assert table_element["text"] == table["markdown"]
    assert [(c["row"], c["col"], c["text"], c["is_header"]) for c in table["cells"]] == [
        (0, 0, "A", True),
        (0, 1, "B", True),
        (1, 0, "1", False),
        (1, 1, "2", False),
    ]
    assert all(c["row_span"] == 1 and c["col_span"] == 1 for c in table["cells"])


def test_prov_page_no_and_bbox_top_left_origin() -> None:
    out = extract(_doc().model_dump())

    [table_element] = [e for e in out["elements"] if e["type"] == "table"]
    assert table_element["page_no"] == 1
    assert table_element["bbox"] == {"l": 72, "t": 100, "r": 300, "b": 180}
    assert table_element["bbox"]["t"] < table_element["bbox"]["b"]
    assert out["pages"] == [{"page_no": 1, "width": 612, "height": 792}]


def test_unknown_label_maps_to_text_and_run_returns_docling_json() -> None:
    doc = DoclingDocument(name="memo")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_title("Memo")
    doc.add_text(label=DocItemLabel.HANDWRITTEN_TEXT, text="Handwritten note")

    expected = extract(doc.model_dump())["elements"]
    assert [e["type"] for e in expected] == ["title", "text"]
    assert expected[1]["text"] == "Handwritten note"

    out = DoclingExtractor().run([Document(content=doc.model_dump_json())])
    assert out["elements"] == expected
    assert json.loads(out["docling_json"]) == json.loads(doc.model_dump_json())
