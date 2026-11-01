---
id: T-worker-004t
kind: test
feature: F-embed
title: 'Write tests: cosine similarity matrix'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_viz_similarity.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_viz_similarity.py && uv run --frozen ruff check tests/unit/test_viz_similarity.py && uv run --frozen pytest -q --collect-only tests/unit/test_viz_similarity.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_similarity.py
max_attempts: 3
---

## Goal
Write unit tests for: cosine similarity matrix. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-004 implements it.

## Context
Stub in `services/worker/src/rag_worker/viz/similarity.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def cosine_matrix(vectors: list[list[float]]) -> list[list[float]]:
    """Square cosine similarity matrix, values clipped to [-1, 1], rounded 6, diagonal exactly 1.0
    (also for zero vectors). [] -> []."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. cosine_matrix([]) == []
2. [[1,0],[0,1],[1,1]] → [[1.0, 0.0, 0.707107], [0.0, 1.0, 0.707107], [0.707107, 0.707107, 1.0]]
3. zero vector row → diagonal still 1.0, off-diagonal 0.0
4. symmetric and all values within [-1, 1]; opposite vectors → -1.0

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
