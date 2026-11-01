---
id: T-worker-015t
kind: test
feature: F-parse
title: 'Write tests: DoclingExtractor (DoclingDocument → elements)'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_docling_extractor.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_docling_extractor.py && uv run --frozen ruff check tests/unit/test_docling_extractor.py && uv run --frozen pytest -q --collect-only tests/unit/test_docling_extractor.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_docling_extractor.py
max_attempts: 3
---

## Goal
Write unit tests for: DoclingExtractor (DoclingDocument → elements). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-015 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. DoclingDocument built in the test (doc.add_title('Report'), doc.add_heading('Intro', level=1), doc.add_text(label=DocItemLabel.TEXT, text='Hello'), a 2x2 table via TableData) → element types ['title', 'heading', 'text', 'table'] in order
2. heading_level: title 1, section_header level 1 → 2; text section_path == ['Report', 'Intro'] (or the heading stack)
3. table element: table.num_rows 2, num_cols 2, cells with row/col/spans, markdown contains '|'; text == markdown
4. items with prov on page 1 and a bbox → page_no 1 and bbox {l,t,r,b} with t < b (top-left origin)
5. unknown label maps to 'text'; DoclingExtractor.run([Document(content=doc.model_dump_json())]) returns the same elements plus docling_json

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
