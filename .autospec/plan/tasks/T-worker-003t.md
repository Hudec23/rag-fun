---
id: T-worker-003t
kind: test
feature: F-embed
title: 'Write tests: PCA + UMAP projections'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_viz_projection.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_viz_projection.py && uv run --frozen ruff check tests/unit/test_viz_projection.py && uv run --frozen pytest -q --collect-only tests/unit/test_viz_projection.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_projection.py
max_attempts: 3
---

## Goal
Write unit tests for: PCA + UMAP projections. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-003 implements it.

## Context
Generate inputs with numpy.random.default_rng(0).normal(size=(n, d)).tolist().

Stub in `services/worker/src/rag_worker/viz/projection.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def pca(vectors: list[list[float]], k: int) -> tuple[list[list[float]] | None, list[float]]:
    """sklearn PCA(n_components=k, random_state=42) -> (coords rounded 6, explained_variance_ratio_
    rounded 6). len(vectors) < k -> (None, []). All-identical vectors -> coords all 0.0 and
    explained variance [] (no exception)."""
    raise NotImplementedError("not implemented")

def umap_project(vectors: list[list[float]], k: int) -> list[list[float]] | None:
    """umap.UMAP(n_components=k, n_neighbors=min(15, n-1), random_state=42, metric='cosine')
    .fit_transform -> rounded 6. n < 5 -> None."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. pca(10 random seeded vectors of dim 8, k=2) → 10 rows of 2 floats, explained variance list of 2 values in [0, 1] summing ≤ 1
2. pca same input twice → identical output (deterministic)
3. pca(vectors of length 1, k=2) → (None, [])
4. pca(5 identical vectors, k=2) → all coords 0.0, explained [] (no exception)
5. umap_project(4 vectors, 2) is None; umap_project(12 seeded vectors, 3) → 12 rows of 3 floats, deterministic

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
