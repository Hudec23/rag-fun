---
id: T-worker-015
kind: impl
feature: F-parse
title: DoclingExtractor (DoclingDocument → elements)
service: worker
depends_on:
- T-worker-015t
edit:
- services/worker/src/rag_worker/components/docling_extractor.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_docling_extractor.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/docling_extractor.py && uv run --frozen ruff check src/rag_worker/components/docling_extractor.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_docling_extractor.py
max_attempts: 3
---

## Goal
Implement: DoclingExtractor (DoclingDocument → elements). The tests written by T-worker-015t define done.

## Context
Build documents with docling_core.types.doc (DoclingDocument, DocItemLabel, TableData, TableCell, ProvenanceItem, BoundingBox, Size). No model files needed.

Stub in `services/worker/src/rag_worker/components/docling_extractor.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""DoclingDocument -> parse elements + pages (strategies docling_layout / docling_ocr)."""
from typing import Any
from haystack import Document, component
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
    raise NotImplementedError("not implemented")

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
        raise NotImplementedError("not implemented")
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
