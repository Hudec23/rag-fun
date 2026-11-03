---
id: T-worker-032t
kind: test
feature: F-retrieve
title: 'Write tests: retrieve pipelines + filters'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_retrieve_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_retrieve_pipeline.py && uv run --frozen ruff check tests/integration/test_retrieve_pipeline.py && uv run --frozen pytest -q --collect-only tests/integration/test_retrieve_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_retrieve_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: retrieve pipelines + filters. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-032 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. to_haystack_filters(empty) is None
2. must [tags any ['hr']] → {'operator': 'AND', 'conditions': [{'field': 'meta.tags', 'operator': 'in', 'value': ['hr']}]}
3. range page gte 1 lte 3 → AND of '>=' 1 and '<=' 3 on 'meta.page'; must_not → {'operator': 'NOT', ...}
4. hybrid over a seeded Qdrant collection (3 docs written with fake dense/sparse embeddings via qdrant_admin.document_store) → per query both dense and sparse lists non-empty; best dense hit for 'vacation days' is the vacation doc
5. filters tags ['tax'] → every returned doc has meta.tags ['tax']
6. mode dense → sparse None; mode sparse → dense None; component names for hybrid include 'dense_retriever' and 'sparse_retriever'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
