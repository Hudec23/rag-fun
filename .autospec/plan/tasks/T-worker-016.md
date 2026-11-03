---
id: T-worker-016
kind: impl
feature: F-parse
title: parse pipelines (docling + plain)
service: worker
depends_on:
- T-worker-016t
- T-worker-014
- T-worker-015
edit:
- services/worker/src/rag_worker/pipelines/parse.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_parse_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/parse.py && uv run --frozen ruff check src/rag_worker/pipelines/parse.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_parse_pipeline.py
max_attempts: 3
---

## Goal
Implement: parse pipelines (docling + plain). The tests written by T-worker-016t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
