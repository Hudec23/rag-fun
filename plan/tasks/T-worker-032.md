---
id: T-worker-032
kind: impl
feature: F-retrieve
title: retrieve pipelines + filters
service: worker
depends_on:
- T-worker-032t
- T-worker-011
edit:
- services/worker/src/rag_worker/pipelines/retrieve.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_retrieve_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/retrieve.py && uv run --frozen ruff check src/rag_worker/pipelines/retrieve.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_retrieve_pipeline.py
max_attempts: 3
---

## Goal
Implement: retrieve pipelines + filters. The tests written by T-worker-032t define done.

## Context
Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards. Seed with FakeModelSet embedders (dims 16).

Stub in `services/worker/src/rag_worker/pipelines/retrieve.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.contracts_gen.shared.common_schema import CollectionRef, PayloadFilter
from rag_worker.models.registry import ModelSet


def to_haystack_filters(f: PayloadFilter) -> dict[str, Any] | None:
    """PayloadFilter -> Haystack filter dict on 'meta.<key>' fields. Empty -> None.
    match.value -> {'field', 'operator': '==', 'value'}; match.any -> 'in' with list; range ->
    AND of '>=' / '<='. must -> AND, should -> OR, must_not -> NOT (each AND-ed together)."""
    raise NotImplementedError("not implemented")

def build_retrieve_pipeline(
    mode: str, collection: CollectionRef, document_store: Any, top_k: int, models: ModelSet
) -> Pipeline:
    """dense: 'dense_embedder' (models.dense_text_embedder) -> 'dense_retriever'
    (QdrantEmbeddingRetriever(document_store, top_k)). sparse: 'sparse_embedder' -> 'sparse_retriever'
    (QdrantSparseEmbeddingRetriever). hybrid: both branches (no joiner in the pipeline; RRF runs after,
    per SYSTEM.md the graph shows both retrievers)."""
    raise NotImplementedError("not implemented")

def run_retrieve(
    pipeline: Pipeline, mode: str, queries: list[str], filters: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """For each query run the pipeline -> [{'query', 'dense': [Document] | None, 'sparse': [...] | None}]."""
    raise NotImplementedError("not implemented")
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
