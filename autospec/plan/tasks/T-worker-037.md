---
id: T-worker-037
kind: impl
feature: F-generate
title: generate pipeline + artifact
service: worker
depends_on:
- T-worker-037t
- T-worker-036
edit:
- services/worker/src/rag_worker/pipelines/generate.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_generate_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/generate.py && uv run --frozen ruff check src/rag_worker/pipelines/generate.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_generate_pipeline.py
max_attempts: 3
---

## Goal
Implement: generate pipeline + artifact. The tests written by T-worker-037t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
