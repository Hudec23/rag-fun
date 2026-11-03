---
id: T-worker-028t
kind: test
feature: F-transform
title: 'Write tests: transform pipeline + artifact'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_transform_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_transform_pipeline.py && uv run --frozen ruff check tests/unit/test_transform_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_transform_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_transform_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: transform pipeline + artifact. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-028 implements it.

## Context
Stub in `services/worker/src/rag_worker/pipelines/transform.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import ModelSet


def build_transform_pipeline(strategy: str, chat: ChatModelConfig, models: ModelSet) -> Pipeline:
    """'prompt' = ChatPromptBuilder(template=[system (prompts.*_SYSTEM by strategy), user
    '{{ question }}'], required_variables='*') -> 'llm' = models.chat_generator(chat, temperature 0.2,
    max_tokens 400) (prompt.prompt -> llm.messages). strategy 'none' -> ValueError (not built)."""
    raise NotImplementedError("not implemented")

def transform_artifact(
    strategy: str,
    question: str,
    reply: str | None,
    messages: list[dict[str, str]],
    chat: ChatModelConfig | None,
    num_queries: int,
) -> dict[str, Any]:
    """contracts/artifacts/transform.schema.json. none -> queries [question], messages [], model None.
    rewrite -> [first non-empty reply line stripped] (empty reply -> [question]). multi_query ->
    [question] + up to num_queries distinct non-empty reply lines (stripped of '- ', '1. ' style
    prefixes, excluding lines equal to question). hyde -> queries [reply.strip()], hyde_document same."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. transform_artifact('none', q, None, [], None, 3) == queries [q], messages [], model None, hyde_document None
2. rewrite with reply '  better query \n second' → queries ['better query']; empty reply → [q]
3. multi_query reply '1. a\n- b\n\nb\nq' with question 'q', num 3 → ['q', 'a', 'b'] (prefixes stripped, duplicates and the question removed)
4. hyde reply ' passage ' → queries ['passage'], hyde_document 'passage'
5. build_transform_pipeline('multi_query', ollama cfg, FakeModelSet()) runs with {'prompt': {'question': 'q', 'n': 3}} and returns a reply; component names {'prompt', 'llm'}; system prompt contains '3 different search queries'
6. build_transform_pipeline('none', …) raises ValueError

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
