---
id: T-worker-024t
kind: test
feature: F-embed
title: 'Write tests: embed pipeline + embed artifact'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_embed_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_embed_pipeline.py && uv run --frozen ruff check tests/unit/test_embed_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_embed_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_embed_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: embed pipeline + embed artifact. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-024 implements it.

## Context
Stub in `services/worker/src/rag_worker/pipelines/embed.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.contracts_gen.shared.common_schema import CollectionRef
from rag_worker.models.registry import ModelSet


def build_embed_pipeline(collection: CollectionRef, batch_size: int, models: ModelSet) -> Pipeline:
    """'dense' (models.dense_document_embedder(collection.dense, batch_size)) -> 'sparse'
    (models.sparse_document_embedder(collection.sparse_model)) -> 'tokens' (TokenView(models.tokenizer
    (collection.dense.model), max_tokens from registry.TOKENIZERS))."""
    raise NotImplementedError("not implemented")

def embed_artifact(
    documents: list[Any], collection: CollectionRef, tokenizer_repo: str, max_tokens: int
) -> dict[str, Any]:
    """Embedded Documents (chunk order) -> embed artifact (contracts/artifacts/embed.schema.json):
    chunks [{index, doc_id, dense (round 6), sparse {indices, values (round 6)}, tokens, token_count,
    over_limit}], sample_indices (viz.sampling), projections (viz.projection pca 2/3 + umap 2/3 over the
    sample), similarity (viz.similarity over the sample)."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. build_embed_pipeline(collection all-minilm 384, 16, FakeModelSet()).run({'dense': {'documents': docs}}) → documents with embedding (384), sparse_embedding and meta token_count
2. embed_artifact(those docs, collection, 'sentence-transformers/all-MiniLM-L6-v2', 256) validates artifacts/embed.schema.json
3. n = 3 chunks → sample_indices [0, 1, 2], similarity 3x3, pca2 3 rows, umap2 None
4. n = 12 → umap2 and umap3 not None
5. dense values rounded to 6 decimals
6. component names {'dense', 'sparse', 'tokens'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
