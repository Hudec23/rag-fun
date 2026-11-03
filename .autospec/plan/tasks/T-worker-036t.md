---
id: T-worker-036t
kind: test
feature: F-generate
title: 'Write tests: context selection + citation parsing'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_context_builder.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_context_builder.py && uv run --frozen ruff check tests/unit/test_context_builder.py && uv run --frozen pytest -q --collect-only tests/unit/test_context_builder.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_context_builder.py
max_attempts: 3
---

## Goal
Write unit tests for: context selection + citation parsing. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-036 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/context_builder.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any


def select_context(
    hits: list[dict[str, Any]], token_counts: list[int], budget_tokens: int
) -> tuple[list[dict[str, Any]], int, int]:
    """Greedy in rank order: include hit i while used + token_counts[i] <= budget_tokens; a hit that
    does not fit is skipped (dropped) and later smaller hits may still fit. Returns
    (included [{'n': 1.., 'hit': hit, 'tokens': t}], used_tokens, dropped_count)."""
    raise NotImplementedError("not implemented")

def parse_citations(answer: str, max_n: int) -> list[int]:
    """Distinct integers n from markers '[n]' or '[n, m]' / '[n,m]' in answer with 1 <= n <= max_n,
    ascending."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. select_context([h1, h2, h3], [100, 50, 30], 140) → h1 fits (100), h2 does not (150 > 140, dropped), h3 fits (130) → included [{n 1, hit h1, tokens 100}, {n 2, hit h3, tokens 30}], used 130, dropped 1
2. budget 0 → included [], used 0, dropped 3
3. parse_citations('A [1] b [2, 3] c [3] d [9]', 3) == [1, 2, 3]
4. parse_citations('[1,2]', 1) == [1]; parse_citations('no cites', 5) == []

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
