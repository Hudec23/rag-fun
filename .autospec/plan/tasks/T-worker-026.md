---
id: T-worker-026
kind: impl
feature: F-store
title: store pipeline + documents_for_store
service: worker
depends_on:
- T-worker-026t
edit:
- services/worker/src/rag_worker/pipelines/store.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_store_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/store.py && uv run --frozen ruff check src/rag_worker/pipelines/store.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_store_pipeline.py
max_attempts: 3
---

## Goal
Implement: store pipeline + documents_for_store. The tests written by T-worker-026t define done.

## Context
Stub in `services/worker/src/rag_worker/pipelines/store.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, Pipeline


def build_store_pipeline(document_store: Any) -> Pipeline:
    """'writer' = DocumentWriter(document_store, policy=DuplicatePolicy.OVERWRITE)."""
    raise NotImplementedError("not implemented")

def documents_for_store(
    chunk_artifact: dict[str, Any],
    embed_artifact: dict[str, Any],
    meta_base: dict[str, Any],
    stored_at: str,
) -> list[Document]:
    """One Document per chunk: id = chunk doc_id, content = chunk text, embedding = dense,
    sparse_embedding = SparseEmbedding(indices, values), meta = payload Meta
    (contracts/qdrant/payload.schema.json): meta_base (file_id, batch_id, batch_name, filename, mime,
    tags, ingest_run_id, dense_model, sparse_model, parse_strategy, chunk_strategy) + page (first of
    page_numbers or None), page_numbers, section_path, element_type, chunk_index, stored_at.
    Chunk/embed index mismatch -> WorkerError('VALIDATION_ERROR', details={'reason': 'chunk/embed mismatch'})."""
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
