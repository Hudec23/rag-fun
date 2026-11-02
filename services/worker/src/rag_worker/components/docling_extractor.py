"""DoclingDocument -> parse elements + pages (strategies docling_layout / docling_ocr)."""

import io
import json
from typing import Any, cast

from docling_core.types.doc import (
    DoclingDocument,
    PictureItem,
    SectionHeaderItem,
    TableItem,
    TextItem,
    TitleItem,
)
from haystack import Document, component

from rag_worker.errors import WorkerError

# Docling DocItemLabel value -> contracts ElementType
LABEL_MAP: dict[str, str] = {
    "title": "title",
    "section_header": "heading",
    "text": "text",
    "paragraph": "text",
    "list_item": "list_item",
    "table": "table",
    "picture": "picture",
    "chart": "picture",
    "caption": "caption",
    "formula": "formula",
    "code": "code",
    "footnote": "footnote",
    "page_header": "page_header",
    "page_footer": "page_footer",
    "checkbox_selected": "text",
    "checkbox_unselected": "text",
    "form": "text",
    "key_value_region": "text",
    "reference": "text",
    "document_index": "text",
}

# origin mimetypes of raster documents (scans) — all their text came from OCR
_SCAN_MIMETYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
    "image/heic",
    "image/heif",
    "image/webp",
}


# Every concrete item yielded by iterate_items carries label + prov (GroupItem does not,
# but group items are never yielded)
Item = TextItem | TableItem | PictureItem


def _element_type(item: Item) -> str:
    """contracts ElementType of a Docling item (unknown labels -> 'text')."""
    return LABEL_MAP.get(item.label.value, "text")


def _text_of(item: Item, doc: DoclingDocument) -> str:
    """Element text: tables -> export_to_markdown, text items -> item.text, else ''."""
    if isinstance(item, TableItem):
        return item.export_to_markdown(doc)
    if isinstance(item, TextItem):
        return item.text
    return ""


def _heading_level(item: Item) -> int | None:
    """title -> 1, section_header -> level + 1 (max 6), other items -> None."""
    if isinstance(item, TitleItem):
        return 1
    if isinstance(item, SectionHeaderItem):
        return min(item.level + 1, 6)
    return None


def _bbox_of(item: Item, doc: DoclingDocument) -> dict[str, float] | None:
    """Top-left-origin bbox of item.prov[0] (None when the item has no prov)."""
    if not item.prov:
        return None
    prov = item.prov[0]
    page = doc.pages.get(prov.page_no)
    bbox = prov.bbox if page is None else prov.bbox.to_top_left_origin(page.size.height)
    return {"l": bbox.l, "t": bbox.t, "r": bbox.r, "b": bbox.b}


def _table_of(item: TableItem, doc: DoclingDocument) -> dict[str, Any]:
    """Table block: num_rows/num_cols/markdown + cells (offsets, spans, header flags)."""
    data = item.data
    cells: list[dict[str, Any]] = []
    for cell in data.table_cells:
        cells.append(
            {
                "row": cell.start_row_offset_idx,
                "col": cell.start_col_offset_idx,
                "row_span": cell.end_row_offset_idx - cell.start_row_offset_idx,
                "col_span": cell.end_col_offset_idx - cell.start_col_offset_idx,
                "text": cell.text,
                "is_header": cell.column_header or cell.row_header,
            }
        )
    return {
        "num_rows": data.num_rows,
        "num_cols": data.num_cols,
        "cells": cells,
        "markdown": item.export_to_markdown(doc),
    }


def _is_from_ocr(item: Item, level: int, doc: DoclingDocument) -> bool:
    """True when the text came from OCR: the item is a child of a picture, or the
    document originated from a raster scan (doc.origin.mimetype)."""
    if level > 1 and item.parent is not None:
        if isinstance(item.parent.resolve(doc), PictureItem):
            return True
    origin = doc.origin
    if origin is not None and origin.mimetype in _SCAN_MIMETYPES:
        return True
    return False


def _page_images(doc: DoclingDocument) -> dict[int, bytes]:
    """PNG bytes of each page image ({} when a page has no image)."""
    images: dict[int, bytes] = {}
    for page_no, page in doc.pages.items():
        image = page.image
        if image is None:
            continue
        pil = image.pil_image
        if pil is None:
            continue
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        images[page_no] = buf.getvalue()
    return images


def extract(doc_json: dict[str, Any]) -> dict[str, Any]:
    """DoclingDocument JSON (docling_core) -> {'elements', 'pages', 'page_images', 'ocr_used'}.
    Iterate doc.iterate_items() in reading order; element type via LABEL_MAP (unknown -> 'text');
    text = item.text, tables -> item.export_to_markdown(doc) + cells from item.data.table_cells
    (row = start_row_offset_idx, col = start_col_offset_idx, spans, is_header = column_header or
    row_header); page_no + bbox from item.prov[0] (bbox.to_top_left_origin(page height)); heading
    level: title 1, section_header item.level + 1 (max 6); section_path = stack of heading texts
    above; from_ocr: picture/scan text produced by OCR (prov on a page whose image is a scan or the
    item is a child of a picture). pages from doc.pages (page_no, size.width, size.height);
    page_images {page_no: PNG bytes} from doc.pages[n].image (when present). ocr_used = any from_ocr."""
    doc = DoclingDocument.model_validate(doc_json)
    elements: list[dict[str, Any]] = []
    sections: list[tuple[str, int]] = []
    for index, (raw_item, level) in enumerate(doc.iterate_items(traverse_pictures=True)):
        item = cast(Item, raw_item)
        text = _text_of(item, doc)
        heading_level = _heading_level(item)
        section_path = [title for title, _ in sections][:10]
        if heading_level is not None:
            while sections and sections[-1][1] >= heading_level:
                sections.pop()
            sections.append((text, heading_level))
        prov = item.prov[0] if item.prov else None
        elements.append(
            {
                "id": f"e-{index:04d}",
                "type": _element_type(item),
                "text": text,
                "page_no": prov.page_no if prov is not None else None,
                "bbox": _bbox_of(item, doc),
                "heading_level": heading_level,
                "section_path": section_path,
                "table": _table_of(item, doc) if isinstance(item, TableItem) else None,
                "from_ocr": _is_from_ocr(item, level, doc),
                "char_start": None,
                "char_end": None,
            }
        )
    pages = [
        {"page_no": page.page_no, "width": page.size.width, "height": page.size.height}
        for page in sorted(doc.pages.values(), key=lambda p: p.page_no)
    ]
    return {
        "elements": elements,
        "pages": pages,
        "page_images": _page_images(doc),
        "ocr_used": any(e["from_ocr"] for e in elements),
    }


@component
class DoclingExtractor:
    """Input: Documents from docling-haystack DoclingConverter(export_type=ExportType.JSON) — one
    Document whose content is the DoclingDocument JSON string."""

    @component.output_types(
        elements=list[dict[str, Any]],
        pages=list[dict[str, Any]],
        page_images=dict[int, bytes],
        ocr_used=bool,
        docling_json=str,
    )
    def run(self, documents: list[Document]) -> dict[str, Any]:
        if not documents:
            raise WorkerError("PARSE_FAILED", details={"reason": "no documents from converter"})
        content = documents[0].content
        if not isinstance(content, str) or not content:
            raise WorkerError("PARSE_FAILED", details={"reason": "empty DoclingDocument JSON"})
        out = extract(json.loads(content))
        out["docling_json"] = content
        return out
