"""parse strategy 'plain_text': no layout model. Supported mimes: application/pdf (pypdf, one 'text'
element per non-empty page, page_no set, no bbox), text/plain + text/markdown (one 'text' element per
blank-line separated block; markdown lines starting with '#' become 'heading' with heading_level =
number of '#'), text/html (tags stripped with html.parser, one 'text' element per block-level
element's text), text/csv (one 'table' element; first row = header). Others ->
WorkerError('UNSUPPORTED_FOR_STRATEGY', details={'mime': mime})."""

import csv
import io
from html.parser import HTMLParser
from typing import Any

from haystack import component
from pypdf import PdfReader

from rag_worker.errors import WorkerError

# Element without char spans: (type, text, page_no, heading_level, table)
type RawItem = tuple[str, str, int | None, int | None, dict[str, Any] | None]

BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "dd",
        "details",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)


def _number(value: float) -> int | float:
    """Normalise a pypdf mediabox size to a plain int (whole numbers) or float."""
    value = float(value)
    return int(value) if value.is_integer() else value


def _pdf(data: bytes) -> tuple[list[RawItem], list[dict[str, Any]]]:
    """pypdf: one 'text' element per non-empty page (page_no set); pages from mediabox sizes."""
    reader = PdfReader(io.BytesIO(data))
    items: list[RawItem] = []
    pages: list[dict[str, Any]] = []
    for page_no, page in enumerate(reader.pages, start=1):
        pages.append(
            {
                "page_no": page_no,
                "width": _number(page.mediabox.width),
                "height": _number(page.mediabox.height),
            }
        )
        text = (page.extract_text() or "").strip()
        if text:
            items.append(("text", text, page_no, None, None))
    return items, pages


def _text_blocks(data: bytes) -> list[list[str]]:
    """UTF-8 (errors='replace') lines grouped into blank-line separated blocks."""
    blocks: list[list[str]] = []
    block: list[str] = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        if line.strip():
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    return blocks


def _text_items(data: bytes, markdown: bool) -> list[RawItem]:
    """text/plain: one 'text' element per blank-line separated block; text/markdown: lines
    starting with '#' become 'heading' with heading_level = number of '#'."""
    items: list[RawItem] = []
    for block in _text_blocks(data):
        if not markdown:
            items.append(("text", "\n".join(block), None, None, None))
            continue
        paragraph: list[str] = []
        for line in block:
            if line.startswith("#"):
                if paragraph:
                    items.append(("text", "\n".join(paragraph), None, None, None))
                    paragraph = []
                level = min(len(line) - len(line.lstrip("#")), 6)
                items.append(("heading", line.lstrip("#").strip(), None, level, None))
            else:
                paragraph.append(line)
        if paragraph:
            items.append(("text", "\n".join(paragraph), None, None, None))
    return items


class _HtmlBlocks(HTMLParser):
    """html.parser collector: the stripped text of each block-level element, in document order.

    Inline elements pass their text through to the innermost open block element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[str] = []
        self._stack: list[list[str]] = [[]]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCK_TAGS:
            self._stack.append([])

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK_TAGS and len(self._stack) > 1:
            text = "".join(self._stack.pop()).strip()
            if text:
                self.items.append(text)

    def handle_data(self, data: str) -> None:
        self._stack[-1].append(data)


def _html(data: bytes) -> list[RawItem]:
    """Tags stripped with html.parser; one 'text' element per block-level element's text."""
    parser = _HtmlBlocks()
    parser.feed(data.decode("utf-8", errors="replace"))
    parser.close()
    return [("text", text, None, None, None) for text in parser.items]


def _padded(row: list[str], num_cols: int) -> list[str]:
    return [row[col] if col < len(row) else "" for col in range(num_cols)]


def _md_row(row: list[str], num_cols: int) -> str:
    """GFM table row '| v1 | v2 |' with pipes escaped."""
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in _padded(row, num_cols)) + " |"


def _csv_item(data: bytes) -> RawItem:
    """One 'table' element; first row = header; the GFM markdown table is the element text."""
    rows = [
        [cell.replace("\n", " ") for cell in row]
        for row in csv.reader(io.StringIO(data.decode("utf-8", errors="replace")))
        if row
    ]
    num_cols = max((len(row) for row in rows), default=0)
    cells = [
        {
            "row": row_no,
            "col": col,
            "row_span": 1,
            "col_span": 1,
            "text": row[col] if col < len(row) else "",
            "is_header": row_no == 0,
        }
        for row_no, row in enumerate(rows)
        for col in range(num_cols)
    ]
    lines: list[str] = []
    if rows:
        lines.append(_md_row(rows[0], num_cols))
        lines.append("|" + "|".join("---" for _ in range(num_cols)) + "|")
        lines.extend(_md_row(row, num_cols) for row in rows[1:])
    markdown = "\n".join(lines)
    table = {
        "num_rows": len(rows),
        "num_cols": num_cols,
        "cells": cells,
        "markdown": markdown,
    }
    return ("table", markdown, None, None, table)


def convert_plain(data: bytes, mime: str) -> dict[str, Any]:
    """-> {'elements': [Element dict without char spans], 'pages': [{'page_no', 'width', 'height'}]}.
    pages: PDF -> one per page with mediabox width/height; others -> []. Text decoded UTF-8 with
    errors='replace'. Element ids e-0000.. in order; section_path built from preceding headings;
    from_ocr False; bbox None; table None except csv."""
    if mime == "application/pdf":
        items, pages = _pdf(data)
    elif mime in ("text/plain", "text/markdown"):
        items = _text_items(data, markdown=mime == "text/markdown")
        pages = []
    elif mime == "text/html":
        items = _html(data)
        pages = []
    elif mime == "text/csv":
        items = [_csv_item(data)]
        pages = []
    else:
        raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"mime": mime})

    elements: list[dict[str, Any]] = []
    headings: list[tuple[int, str]] = []
    for index, (el_type, text, page_no, level, table) in enumerate(items):
        if level is not None:
            while headings and headings[-1][0] >= level:
                headings.pop()
        section_path = [heading_text for _, heading_text in headings]
        if level is not None:
            headings.append((level, text))
        elements.append(
            {
                "id": f"e-{index:04d}",
                "type": el_type,
                "text": text,
                "page_no": page_no,
                "bbox": None,
                "heading_level": level,
                "section_path": section_path[:10],
                "table": table,
                "from_ocr": False,
            }
        )
    return {"elements": elements, "pages": pages}


@component
class PlainTextConverter:
    @component.output_types(elements=list[dict[str, Any]], pages=list[dict[str, Any]])
    def run(self, data: bytes, mime: str) -> dict[str, Any]:
        return convert_plain(data, mime)
