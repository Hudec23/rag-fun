---
id: T-worker-031t
kind: test
feature: F-retrieve
title: 'Write tests: RRF fusion'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_rrf.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_rrf.py && uv run --frozen ruff check tests/unit/test_rrf.py && uv run --frozen pytest -q --collect-only tests/unit/test_rrf.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_rrf.py
max_attempts: 3
---

## Goal
Write unit tests for: RRF fusion. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-031 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/rrf.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, component


def rrf_fuse(
    lists: list[tuple[int, str, list[Document]]], rrf_k: int, top_k: int
) -> list[dict[str, Any]]:
    """lists = [(query_index, 'dense'|'sparse', ranked docs)]. score(d) = Σ 1/(rrf_k + rank) over
    every list containing d (rank 1-based; identity = doc.id). Sort score desc, then doc.id asc;
    keep top_k. Returns [{'doc': Document, 'score': float(round 6), 'source_ranks':
    [{'query_index', 'list', 'rank'}]}] with source_ranks in input-list order."""
    raise NotImplementedError("not implemented")

@component
class RRFJoiner:
    def __init__(self, rrf_k: int, top_k: int) -> None:
        self.rrf_k = rrf_k
        self.top_k = top_k

    @component.output_types(fused=list[dict[str, Any]])
    def run(self, lists: list[tuple[int, str, list[Document]]]) -> dict[str, Any]:
        return {"fused": rrf_fuse(lists, self.rrf_k, self.top_k)}
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. lists dense [A, B], sparse [B, C] with rrf_k 60 → order [B, A, C]; B score round(1/62 + 1/61, 6)
2. source_ranks of B == [{'query_index': 0, 'list': 'dense', 'rank': 2}, {'query_index': 0, 'list': 'sparse', 'rank': 1}]
3. ties broken by doc.id ascending
4. top_k 2 truncates
5. two queries contribute to the same doc (query_index 0 and 1)
6. empty input → []

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
