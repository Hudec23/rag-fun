---
id: T-worker-028
kind: impl
feature: F-transform
title: transform pipeline + artifact
service: worker
depends_on:
- T-worker-028t
edit:
- services/worker/src/rag_worker/pipelines/transform.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_transform_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/transform.py && uv run --frozen ruff check src/rag_worker/pipelines/transform.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_transform_pipeline.py
max_attempts: 3
---

## Goal
Implement: transform pipeline + artifact. The tests written by T-worker-028t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
