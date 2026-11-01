---
id: T-worker-034t
kind: test
feature: F-rerank
title: 'Write tests: rerank pipeline + artifact'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_rerank_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_rerank_pipeline.py && uv run --frozen ruff check tests/unit/test_rerank_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_rerank_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_rerank_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: rerank pipeline + artifact. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-034 implements it.

## Context
Stub in `services/worker/src/rag_worker/pipelines/rerank.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.models.registry import ModelSet


def build_rerank_pipeline(model: str, top_n: int, models: ModelSet) -> Pipeline:
    """'ranker' = models.ranker(model, top_n)."""
    raise NotImplementedError("not implemented")

def rerank_artifact(
    enabled: bool,
    model: str | None,
    top_n: int,
    query: str,
    before: list[dict[str, Any]],
    reranked: list[Any] | None,
) -> dict[str, Any]:
    """contracts/artifacts/rerank.schema.json. enabled: after[i] = {'hit': to_hit(doc, rank i+1,
    score), 'previous_rank': rank of doc_id in before, 'rerank_score': score}; ties already ordered by
    the ranker, re-sort score desc then doc_id asc. disabled: after = before[:top_n] with
    previous_rank = rank, rerank_score None, model None."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. rerank_artifact(True, model, 2, q, before=FIXTURES artifact_retrieve fused hits, reranked docs [d3, d1] with scores 0.9, 0.5) → after[0].hit.doc_id == d3, previous_rank == rank of d3 in before, rerank_score 0.9, hit.rank 1
2. disabled → after == before[:top_n] with previous_rank == rank, rerank_score None, model None
3. artifact validates artifacts/rerank.schema.json
4. build_rerank_pipeline(model, 2, FakeModelSet()).run({'ranker': {'query': 'tax refund', 'documents': docs}}) → 2 docs, best overlap first; component names {'ranker'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
