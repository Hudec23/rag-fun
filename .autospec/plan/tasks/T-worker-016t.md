---
id: T-worker-016t
kind: test
feature: F-parse
title: 'Write tests: parse pipelines (docling + plain)'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_parse_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_parse_pipeline.py && uv run --frozen ruff check tests/integration/test_parse_pipeline.py && uv run --frozen pytest -q --collect-only tests/integration/test_parse_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_parse_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: parse pipelines (docling + plain). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-016 implements it.

## Context
Uses the real Docling models baked into the worker-dev image (slow: allow ~60 s). Samples in tests.conftest.SAMPLES.

Stub in `services/worker/src/rag_worker/pipelines/parse.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline


def build_parse_pipeline(strategy: str, params: dict[str, Any]) -> Pipeline:
    """docling_layout / docling_ocr: 'converter' = docling-haystack DoclingConverter(converter=
    DocumentConverter with PdfPipelineOptions(artifacts_path=$DOCLING_ARTIFACTS_PATH,
    do_table_structure=params.extract_tables, generate_page_images=params.page_images,
    images_scale=1.5, do_ocr=True, ocr_options=EasyOcrOptions(lang=['en'],
    force_full_page_ocr=(strategy == 'docling_ocr'))) for PDF and image formats, default options for
    office/html/md/csv), export_type=ExportType.JSON) -> 'extractor' = DoclingExtractor
    (import: from haystack_integrations.components.converters.docling import DoclingConverter, ExportType)
    (converter.documents -> extractor.documents).
    plain_text: single component 'converter' = PlainTextConverter."""
    raise NotImplementedError("not implemented")

def run_parse(
    pipeline: Pipeline, strategy: str, data: bytes, mime: str, filename: str
) -> dict[str, Any]:
    """Run the pipeline (docling: sources=[ByteStream(data, meta={'file_name': filename}, mime_type=
    mime)]) -> {'elements', 'pages', 'page_images' ({} for plain_text), 'ocr_used', 'docling_json'
    (None for plain_text)}. Docling conversion error -> WorkerError('PARSE_FAILED',
    details={'reason': str(e)[:300]})."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. plain_text pipeline on handbook.md → elements non-empty, page_images {}, docling_json None, ocr_used False
2. docling_layout on q3-report.pdf (page_images True) → 2 pages, page_images keys {1, 2} with PNG magic bytes, docling_json is a JSON string, 'Revenue grew 12 percent' in some element text
3. docling_layout with page_images False → page_images {}
4. docling_ocr on scan-invoice.png → ocr_used True and 'invoice' in joined text (lowercase)
5. corrupted PDF bytes (b'%PDF-1.4 garbage') → WorkerError PARSE_FAILED
6. pipeline component names: docling → {'converter', 'extractor'}; plain_text → {'converter'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
