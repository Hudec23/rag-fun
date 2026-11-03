---
id: T-worker-019t
kind: test
feature: F-chunk
title: 'Write tests: TableChunker'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_table_chunker.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_table_chunker.py && uv run --frozen ruff check tests/unit/test_table_chunker.py && uv run --frozen pytest -q --collect-only tests/unit/test_table_chunker.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_table_chunker.py
max_attempts: 3
---

## Goal
Write unit tests for: TableChunker. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-019 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/table_chunker.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, component


def table_documents(elements: list[dict[str, Any]], row_chunks: bool) -> list[Document]:
    """One Document per table element: content = table.markdown, meta element_ids [id], page_numbers
    [page_no] (or []), section_path, element_type 'table', split_idx_start = element char_start.
    row_chunks: additionally per data row (not header rows) a Document with content lines
    '<header>: <cell>' joined by '\\n' (header = header cell text of that column, or 'col<N>'),
    meta no_span True, element_type 'table'. Order: table chunk, then its row chunks."""
    raise NotImplementedError("not implemented")

@component
class TableChunker:
    """Tables -> table_documents; non-table text -> RecursiveDocumentSplitter(split_length=
    text_length, split_overlap=text_overlap, split_unit='char') over each maximal run of consecutive
    non-table elements (as one Document with split_idx offset of the run). Output documents ordered
    by source position."""

    def __init__(self, row_chunks: bool, text_length: int, text_overlap: int) -> None:
        self.row_chunks = row_chunks
        self.text_length = text_length
        self.text_overlap = text_overlap

    @component.output_types(documents=list[Document])
    def run(self, elements: list[dict[str, Any]], source_text: str) -> dict[str, Any]:
        raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. table_documents([table element of FIXTURE-like 2x2 table]) → 1 Document with content == markdown, meta element_type 'table', element_ids [id]
2. row_chunks True with header ['product','price'] and rows ['Basic','9'], ['Pro','29'] → table doc + 2 row docs 'product: Basic\nprice: 9' and 'product: Pro\nprice: 29' with meta no_span True
3. header cell missing → 'col<N>' label
4. TableChunker(False, 50, 0).run(elements [text 60 chars, table, text 10 chars], source_text) → documents ordered by position: text chunks, table, text; table chunk split_idx_start == table char_start
5. no tables → only recursive text chunks

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
