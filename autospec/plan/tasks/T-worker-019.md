---
id: T-worker-019
kind: impl
feature: F-chunk
title: TableChunker
service: worker
depends_on:
- T-worker-019t
edit:
- services/worker/src/rag_worker/components/table_chunker.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_table_chunker.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/table_chunker.py && uv run --frozen ruff check src/rag_worker/components/table_chunker.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_table_chunker.py
max_attempts: 3
---

## Goal
Implement: TableChunker. The tests written by T-worker-019t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
