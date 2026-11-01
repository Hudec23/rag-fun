---
id: T-worker-023
kind: impl
feature: F-embed
title: TokenView component
service: worker
depends_on:
- T-worker-023t
- T-worker-012
edit:
- services/worker/src/rag_worker/components/token_view.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_token_view.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/token_view.py && uv run --frozen ruff check src/rag_worker/components/token_view.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_token_view.py
max_attempts: 3
---

## Goal
Implement: TokenView component. The tests written by T-worker-023t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
