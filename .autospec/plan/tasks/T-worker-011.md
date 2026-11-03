---
id: T-worker-011
kind: impl
feature: F-store
title: qdrant_admin document_store + deletes
service: worker
depends_on:
- T-worker-011t
edit:
- services/worker/src/rag_worker/qdrant_admin.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_qdrant_admin.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/qdrant_admin.py && uv run --frozen ruff check src/rag_worker/qdrant_admin.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_qdrant_admin.py
max_attempts: 3
---

## Goal
Implement: qdrant_admin document_store + deletes. The tests written by T-worker-011t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
