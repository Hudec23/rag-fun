"""Unit tests for PlainTextConverter (parse strategy 'plain_text'): build inputs from SAMPLES bytes,
call the component's run() directly, assert exact dicts. PlainTextConverter is a stub — every test
here is red until T-worker-014."""

from typing import Any

import pytest

from rag_worker.components.plain_text_converter import PlainTextConverter
from rag_worker.errors import WorkerError
from tests.conftest import SAMPLES

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _convert(name: str, mime: str) -> dict[str, Any]:
    return PlainTextConverter().run(data=(SAMPLES / name).read_bytes(), mime=mime)


def test_markdown_headings_and_section_path() -> None:
    out = _convert("handbook.md", "text/markdown")

    assert out["pages"] == []
    elements = out["elements"]
    assert [e["id"] for e in elements] == [f"e-{i:04d}" for i in range(7)]
    assert [e["type"] for e in elements] == [
        "heading",
        "heading",
        "text",
        "heading",
        "text",
        "heading",
        "text",
    ]
    assert elements[0]["text"] == "Employee Handbook"
    assert elements[0]["heading_level"] == 1
    assert elements[0]["section_path"] == []
    assert elements[1]["text"] == "Vacation"
    assert elements[1]["heading_level"] == 2
    assert elements[1]["section_path"] == ["Employee Handbook"]
    assert elements[2]["text"] == (
        "Every employee has 25 vacation days per year. Unused days expire at the end of March."
    )
    assert elements[2]["heading_level"] is None
    assert elements[2]["section_path"] == ["Employee Handbook", "Vacation"]
    assert elements[3]["text"] == "Remote work"
    assert elements[3]["heading_level"] == 2
    assert elements[3]["section_path"] == ["Employee Handbook"]
    assert elements[4]["text"] == (
        "Remote work is allowed up to three days per week. Equipment is provided by the IT team."
    )
    assert elements[4]["section_path"] == ["Employee Handbook", "Remote work"]
    assert elements[5]["text"] == "Expenses"
    assert elements[5]["heading_level"] == 2
    assert elements[5]["section_path"] == ["Employee Handbook"]
    assert (
        elements[6]["text"]
        == "Travel expenses are reimbursed within 14 days after the receipt is uploaded."
    )
    assert elements[6]["section_path"] == ["Employee Handbook", "Expenses"]
    assert all(e["from_ocr"] is False and e["bbox"] is None for e in elements)
    assert all(e["table"] is None for e in elements)


def test_plain_text_blank_line_blocks_and_no_pages() -> None:
    out = _convert("notes.txt", "text/plain")

    assert out["pages"] == []
    elements = out["elements"]
    assert [e["id"] for e in elements] == ["e-0000", "e-0001", "e-0002"]
    assert [e["type"] for e in elements] == ["text", "text", "text"]
    assert [e["text"] for e in elements] == [
        "Meeting notes.",
        "The tax refund rules changed in 2026.",
        "Refunds are now processed monthly.",
    ]
    assert all(e["section_path"] == [] for e in elements)
    assert all(e["heading_level"] is None for e in elements)
    assert all(e["from_ocr"] is False and e["bbox"] is None for e in elements)


def test_csv_one_table_element_with_header() -> None:
    out = _convert("prices.csv", "text/csv")

    assert out["pages"] == []
    [element] = out["elements"]
    assert element["id"] == "e-0000"
    assert element["type"] == "table"
    assert element["section_path"] == []
    assert element["from_ocr"] is False
    assert element["bbox"] is None
    table = element["table"]
    assert table["num_rows"] == 4
    assert table["num_cols"] == 3
    assert table["markdown"].startswith("| product | price_eur | plan |")
    assert element["text"] == table["markdown"]
    assert [(c["row"], c["col"], c["text"], c["is_header"]) for c in table["cells"]] == [
        (0, 0, "product", True),
        (0, 1, "price_eur", True),
        (0, 2, "plan", True),
        (1, 0, "Basic", False),
        (1, 1, "9", False),
        (1, 2, "monthly", False),
        (2, 0, "Pro", False),
        (2, 1, "29", False),
        (2, 2, "monthly", False),
        (3, 0, "Team", False),
        (3, 1, "99", False),
        (3, 2, "yearly", False),
    ]
    assert all(c["row_span"] == 1 and c["col_span"] == 1 for c in table["cells"])


def test_html_block_level_elements_become_texts() -> None:
    out = _convert("faq.html", "text/html")

    assert out["pages"] == []
    elements = out["elements"]
    assert [e["id"] for e in elements] == ["e-0000", "e-0001", "e-0002"]
    assert [e["type"] for e in elements] == ["text", "text", "text"]
    assert elements[0]["text"] == "FAQ"
    assert (
        elements[1]["text"] == "How do I reset my password? Use the reset link on the login page."
    )
    assert elements[2]["text"] == "Where are invoices? Under Billing."
    assert all(e["section_path"] == [] for e in elements)
    assert all(e["from_ocr"] is False and e["bbox"] is None for e in elements)


def test_pdf_one_text_element_per_page_and_page_sizes() -> None:
    out = _convert("q3-report.pdf", "application/pdf")

    assert out["pages"] == [
        {"page_no": 1, "width": 612, "height": 792},
        {"page_no": 2, "width": 612, "height": 792},
    ]
    elements = out["elements"]
    assert [e["id"] for e in elements] == ["e-0000", "e-0001"]
    assert [e["type"] for e in elements] == ["text", "text"]
    assert [e["page_no"] for e in elements] == [1, 2]
    assert elements[0]["text"].startswith("Q3 Report")
    assert "Revenue grew 12 percent year over year" in elements[0]["text"]
    assert "Europe contributed most of the new subscription revenue." in elements[0]["text"]
    assert elements[1]["text"].startswith("Outlook")
    assert "The board approved a dividend of 0.40 EUR per share." in elements[1]["text"]
    assert all(e["from_ocr"] is False and e["bbox"] is None for e in elements)


def test_unsupported_mimes_raise_worker_error() -> None:
    for name, mime in [("scan-invoice.png", "image/png"), ("contract.docx", DOCX_MIME)]:
        with pytest.raises(WorkerError) as excinfo:
            _convert(name, mime)
        assert excinfo.value.error_body() == {
            "code": "UNSUPPORTED_FOR_STRATEGY",
            "message": "This file type cannot be processed with the chosen strategy",
            "details": {"mime": mime},
        }
