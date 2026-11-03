---
id: T-worker-013t
kind: test
feature: F-parse
title: 'Write tests: assign_spans (full_text + char spans)'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_text_layout.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_text_layout.py && uv run --frozen ruff check tests/unit/test_text_layout.py && uv run --frozen pytest -q --collect-only tests/unit/test_text_layout.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_text_layout.py
max_attempts: 3
---

## Goal
Write unit tests for: assign_spans (full_text + char spans). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-013 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/text_layout.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any


def assign_spans(elements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Build parse full_text and char spans (contracts/artifacts/parse.schema.json description):
    full_text = texts of elements that are non-empty and not page_header/page_footer, joined with
    '\\n\\n'; each such element gets char_start/char_end (exclusive) into full_text; the others get
    None/None. Returns (new element dicts, full_text); input not mutated."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. [text 'A', text 'B'] → full_text 'A\n\nB', spans (0,1) and (3,4)
2. page_header/page_footer and empty-text elements get char_start/char_end None and are not in full_text
3. input list is not mutated (deep-compare a copy)
4. unicode text 'čaj' → span length 3
5. [] → ([], '')

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
