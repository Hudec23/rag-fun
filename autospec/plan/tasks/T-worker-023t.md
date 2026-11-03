---
id: T-worker-023t
kind: test
feature: F-embed
title: 'Write tests: TokenView component'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_token_view.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_token_view.py && uv run --frozen ruff check tests/unit/test_token_view.py && uv run --frozen pytest -q --collect-only tests/unit/test_token_view.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_token_view.py
max_attempts: 3
---

## Goal
Write unit tests for: TokenView component. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-023 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/token_view.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, component
MAX_TOKENS_SHOWN = 2048


def tokenize(tokenizer: Any, text: str, max_tokens: int) -> dict[str, Any]:
    """enc = tokenizer.encode(text) (special tokens included) -> {'tokens': enc.tokens[:2048],
    'token_count': len(enc.ids), 'over_limit': len(enc.ids) > max_tokens}."""
    raise NotImplementedError("not implemented")

@component
class TokenView:
    """Adds meta 'tokens', 'token_count', 'over_limit' to each Document (tokenize)."""

    def __init__(self, tokenizer: Any, max_tokens: int) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    @component.output_types(documents=list[Document])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. tokenize(all-minilm tokenizer, 'Hello world', 256) == {'tokens': ['[CLS]', 'hello', 'world', '[SEP]'], 'token_count': 4, 'over_limit': False}
2. text of 300 words with max_tokens 256 → over_limit True, token_count > 256
3. very long text → tokens truncated to 2048 entries but token_count is the full count
4. TokenView.run(documents) returns copies with meta tokens/token_count/over_limit (originals unchanged)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
