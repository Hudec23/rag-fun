---
id: T-worker-026t
kind: test
feature: F-store
title: 'Write tests: store pipeline + documents_for_store'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_store_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_store_pipeline.py && uv run --frozen ruff check tests/unit/test_store_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_store_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_store_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: store pipeline + documents_for_store. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-026 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. documents_for_store(FIXTURES artifact_chunk, artifact_embed, meta_base, ts) → 4 Documents with id == chunk doc_id, embedding == dense, sparse_embedding indices/values, meta validating qdrant/payload.schema.json#/$defs/Meta
2. meta.page == first page number or None when page_numbers is []
3. index mismatch (embed artifact with 3 chunks) → WorkerError VALIDATION_ERROR
4. build_store_pipeline(InMemoryDocumentStore()) writes the documents (store.count_documents() == 4); writing twice keeps 4 (OVERWRITE)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
