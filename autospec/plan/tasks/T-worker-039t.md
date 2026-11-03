---
id: T-worker-039t
kind: test
feature: F-pipeline-graph
title: 'Write tests: pipeline graph export'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_graphs.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_graphs.py && uv run --frozen ruff check tests/unit/test_graphs.py && uv run --frozen pytest -q --collect-only tests/unit/test_graphs.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_graphs.py
max_attempts: 3
---

## Goal
Write unit tests for: pipeline graph export. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-039 implements it.

## Context
Stub in `services/worker/src/rag_worker/pipelines/graphs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.models.registry import ModelSet
VARIANTS: list[tuple[str, str]] = (
    [("parse", v) for v in ("docling_layout", "docling_ocr", "plain_text")]
    + [("chunk", v) for v in ("fixed", "sentence", "recursive", "semantic", "structure", "table")]
    + [("embed", "default"), ("store", "default")]
    + [("transform", v) for v in ("rewrite", "multi_query", "hyde")]
    + [("retrieve", v) for v in ("dense", "sparse", "hybrid")]
    + [("rerank", "default"), ("generate", "default")]
)


def graph_of(pipeline: Pipeline, stage: str, variant: str) -> dict[str, Any]:
    """pipeline.to_dict() -> {'stage', 'variant', 'nodes': [{'name', 'type', 'custom':
    type.startswith('rag_worker.components'), 'init_params': [{'name', 'value': json.dumps(value,
    default=str)[:2000]}] (keys containing 'key', 'token' or 'secret' -> value '"***"')}], 'edges':
    [{'sender', 'sender_socket', 'receiver', 'receiver_socket'}] from to_dict()['connections']
    ('a.out' -> sender a, socket out)}. Nodes sorted by name, edges in to_dict order."""
    raise NotImplementedError("not implemented")

def all_graphs(models: ModelSet, qdrant_url: str) -> list[dict[str, Any]]:
    """Build every VARIANTS pipeline (19 pairs) with default params (contracts defaults) and a placeholder
    collection (bge-m3, 1024 dims, Qdrant/bm25, qdrant name rf_000…0, Ollama chat qwen3:8b) and
    return graph_of for each, in VARIANTS order. Must not contact any server."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. all_graphs(FakeModelSet(), 'http://127.0.0.1:1') returns 19 graphs in VARIANTS order, each validating shared/pipeline-graph.schema.json, without network (socket guard)
2. chunk/semantic graph has node 'splitter' with custom True and type ending 'SemanticSplitter'; edge splitter.documents → annotator.documents
3. retrieve/hybrid nodes include dense_embedder, dense_retriever, sparse_embedder, sparse_retriever
4. init param named 'api_key' (anthropic chat cfg in a graph_of call) → value '"***"'
5. nodes sorted by name

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
