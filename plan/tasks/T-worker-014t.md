---
id: T-worker-014t
kind: test
feature: F-parse
title: 'Write tests: PlainTextConverter'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_plain_text_converter.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_plain_text_converter.py && uv run --frozen ruff check tests/unit/test_plain_text_converter.py && uv run --frozen pytest -q --collect-only tests/unit/test_plain_text_converter.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_plain_text_converter.py
max_attempts: 3
---

## Goal
Write unit tests for: PlainTextConverter. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-014 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. markdown SAMPLES/handbook.md → first element heading 'Employee Handbook' level 1, 'Vacation' level 2, paragraph section_path ['Employee Handbook', 'Vacation']
2. text/plain notes.txt → 3 text elements (blank-line blocks), ids e-0000..e-0002, pages []
3. text/csv prices.csv → one table element: num_rows 4, num_cols 3, header cells is_header True, markdown starts '| product | price_eur | plan |'
4. text/html faq.html → first element text 'FAQ', followed by the two <p> texts
5. application/pdf q3-report.pdf → 2 text elements with page_no 1 and 2; pages [{page_no 1, width 612, height 792}, …]
6. image/png → WorkerError UNSUPPORTED_FOR_STRATEGY details {'mime': 'image/png'}; docx mime → same code

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
