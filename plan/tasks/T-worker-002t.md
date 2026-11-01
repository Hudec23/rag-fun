---
id: T-worker-002t
kind: test
feature: F-embed
title: 'Write tests: sample_indices'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_viz_sampling.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_viz_sampling.py && uv run --frozen ruff check tests/unit/test_viz_sampling.py && uv run --frozen pytest -q --collect-only tests/unit/test_viz_sampling.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_sampling.py
max_attempts: 3
---

## Goal
Write unit tests for: sample_indices. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-002 implements it.

## Context
Stub in `services/worker/src/rag_worker/viz/sampling.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def sample_indices(n: int, cap: int = 200) -> list[int]:
    """Evenly spaced indices: [round(x) for x in numpy.linspace(0, n-1, min(n, cap))] as ints,
    strictly increasing and unique. n = 0 -> []; n <= cap -> list(range(n))."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. sample_indices(0) == []; sample_indices(1) == [0]
2. sample_indices(5) == [0, 1, 2, 3, 4]
3. sample_indices(1000) has length 200, starts 0, ends 999, strictly increasing ints
4. sample_indices(10, cap=3) == [0, 4, 9] (round(linspace(0, 9, 3)) = 0, 4.5→4 (banker's), 9) — assert len 3, first 0, last 9, unique

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
