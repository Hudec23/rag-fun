---
id: T-worker-014
kind: impl
feature: F-parse
title: PlainTextConverter
service: worker
depends_on:
- T-worker-014t
- T-worker-013
edit:
- services/worker/src/rag_worker/components/plain_text_converter.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_plain_text_converter.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/plain_text_converter.py && uv run --frozen ruff check src/rag_worker/components/plain_text_converter.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_plain_text_converter.py
max_attempts: 3
---

## Goal
Implement: PlainTextConverter. The tests written by T-worker-014t define done.

## Context
Read sample bytes from tests.conftest.SAMPLES.

Stub in `services/worker/src/rag_worker/components/plain_text_converter.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""parse strategy 'plain_text': no layout model. Supported mimes: application/pdf (pypdf, one 'text'
element per non-empty page, page_no set, no bbox), text/plain + text/markdown (one 'text' element per
blank-line separated block; markdown lines starting with '#' become 'heading' with heading_level =
number of '#'), text/html (tags stripped with html.parser, one 'text' element per block-level
element's text), text/csv (one 'table' element; first row = header). Others ->
WorkerError('UNSUPPORTED_FOR_STRATEGY', details={'mime': mime})."""
from typing import Any
from haystack import component


def convert_plain(data: bytes, mime: str) -> dict[str, Any]:
    """-> {'elements': [Element dict without char spans], 'pages': [{'page_no', 'width', 'height'}]}.
    pages: PDF -> one per page with mediabox width/height; others -> []. Text decoded UTF-8 with
    errors='replace'. Element ids e-0000.. in order; section_path built from preceding headings;
    from_ocr False; bbox None; table None except csv."""
    raise NotImplementedError("not implemented")

@component
class PlainTextConverter:
    @component.output_types(elements=list[dict[str, Any]], pages=list[dict[str, Any]])
    def run(self, data: bytes, mime: str) -> dict[str, Any]:
        return convert_plain(data, mime)
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
