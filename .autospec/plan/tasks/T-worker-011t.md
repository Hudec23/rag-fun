---
id: T-worker-011t
kind: test
feature: F-store
title: 'Write tests: qdrant_admin document_store + deletes'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_qdrant_admin.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_qdrant_admin.py && uv run --frozen ruff check tests/integration/test_qdrant_admin.py && uv run --frozen pytest -q --collect-only tests/integration/test_qdrant_admin.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_qdrant_admin.py
max_attempts: 3
---

## Goal
Write unit tests for: qdrant_admin document_store + deletes. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-011 implements it.

## Context
Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards.

Stub in `services/worker/src/rag_worker/qdrant_admin.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Qdrant writes owned by the worker (collection lifecycle, deletes). Sync qdrant_client.QdrantClient;
call from asyncio.to_thread."""
from typing import Any
from qdrant_client import QdrantClient
KEYWORD_INDEXES = [
    "meta.file_id",
    "meta.batch_id",
    "meta.tags",
    "meta.mime",
    "meta.element_type",
    "meta.chunk_strategy",
    "meta.parse_strategy",
]
INTEGER_INDEXES = ["meta.page", "meta.chunk_index"]


def document_store(qdrant_url: str, qdrant_name: str, dims: int) -> Any:
    """QdrantDocumentStore(url=qdrant_url, index=qdrant_name, embedding_dim=dims, similarity='cosine',
    use_sparse_embeddings=True, sparse_idf=True, recreate_index=False, return_embedding=False,
    wait_result_from_api=True, payload_fields_to_index=[{'field_name': k, 'field_schema': 'keyword'}
    for KEYWORD_INDEXES] + [... 'integer' for INTEGER_INDEXES])."""
    raise NotImplementedError("not implemented")

def delete_file_points(client: QdrantClient, qdrant_name: str, file_id: str) -> int:
    """Delete points with meta.file_id == file_id; return how many existed before (count exact).
    Missing collection -> 0."""
    raise NotImplementedError("not implemented")

def drop_collection(client: QdrantClient, qdrant_name: str) -> None:
    """Delete collection if it exists."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. document_store(url, name, 4) then write 2 Documents (embedding 4 floats, sparse_embedding, meta file_id 'f1') via store.write_documents → collection has named vectors 'text-dense' size 4 and sparse 'text-sparse' with modifier IDF; payload index 'meta.file_id' exists (keyword)
2. delete_file_points(client, name, 'f1') → returns 2, count afterwards 0; other file ids untouched
3. delete_file_points on a missing collection → 0
4. drop_collection removes it; dropping again does not raise

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
