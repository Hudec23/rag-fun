---
id: T-worker-001t
kind: test
feature: F-chunk
title: 'Write tests: chunk_stats'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_viz_stats.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_viz_stats.py && uv run --frozen ruff check tests/unit/test_viz_stats.py && uv run --frozen pytest -q --collect-only tests/unit/test_viz_stats.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_stats.py
max_attempts: 3
---

## Goal
Write unit tests for: chunk_stats. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-001 implements it.

## Context
Stub in `services/worker/src/rag_worker/viz/stats.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any


def chunk_stats(char_counts: list[int]) -> dict[str, Any]:
    """chunk artifact 'stats': count, min_chars, max_chars, mean_chars (round 2), histogram =
    numpy.histogram(char_counts, bins=min(20, max(1, count))) with bin_edges rounded to 2 decimals.
    Empty list -> count 0, min/max/mean 0, bin_edges [], counts []."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. chunk_stats([]) == {'count': 0, 'min_chars': 0, 'max_chars': 0, 'mean_chars': 0, 'histogram': {'bin_edges': [], 'counts': []}}
2. chunk_stats([10]) → count 1, min = max = 10, mean 10.0, len(counts) == 1, sum(counts) == 1
3. chunk_stats([10, 20, 30, 40]) → mean 25.0, bins == 4, len(bin_edges) == 5, bin_edges[0] == 10.0, bin_edges[-1] == 40.0
4. 25 values → exactly 20 bins; sum(counts) == 25
5. mean rounded to 2 decimals: [1, 2, 2] → 1.67

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
