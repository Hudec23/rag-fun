---
id: T-worker-037t
kind: test
feature: F-generate
title: 'Write tests: generate pipeline + artifact'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_generate_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_generate_pipeline.py && uv run --frozen ruff check tests/unit/test_generate_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_generate_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_generate_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: generate pipeline + artifact. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-037 implements it.

## Context
Stub in `services/worker/src/rag_worker/pipelines/generate.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from collections.abc import Callable
from typing import Any
from haystack import Pipeline
from haystack.dataclasses import StreamingChunk
from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import ModelSet


def build_generate_pipeline(
    chat: ChatModelConfig,
    temperature: float,
    max_tokens: int,
    models: ModelSet,
    streaming_callback: Callable[[StreamingChunk], None] | None,
) -> Pipeline:
    """'prompt' = ChatPromptBuilder([system prompts.ANSWER_SYSTEM, user prompts.ANSWER_USER],
    required_variables='*') -> 'llm' = models.chat_generator(chat, temperature, max_tokens,
    streaming_callback)."""
    raise NotImplementedError("not implemented")

def generate_artifact(
    chat: ChatModelConfig,
    messages: list[dict[str, str]],
    budget: dict[str, int],
    context: list[dict[str, Any]],
    answer: str,
    usage: dict[str, int | None],
) -> dict[str, Any]:
    """contracts/artifacts/generate.schema.json; citations = context_builder.parse_citations(answer,
    len(context))."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. build_generate_pipeline(ollama cfg, 0.2, 100, FakeModelSet(), cb).run({'prompt': {'context': [{'n': 1, 'text': 'x'}], 'question': 'q'}}) → replies[0].text == 'Fake answer to: Context: [1]' (first line of the user message is 'Context:'); the streaming callback chunks join to that text; component names {'prompt', 'llm'}
2. the user message contains '[1] x' and 'Question: q'; system message == prompts.ANSWER_SYSTEM
3. generate_artifact(..., answer 'a [1] [2]', context of 1) → citations [1]; validates artifacts/generate.schema.json
4. usage passed through (None values allowed)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
