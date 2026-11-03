---
id: T-worker-036
kind: impl
feature: F-generate
title: context selection + citation parsing
service: worker
depends_on:
- T-worker-036t
edit:
- services/worker/src/rag_worker/components/context_builder.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_context_builder.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/context_builder.py && uv run --frozen ruff check src/rag_worker/components/context_builder.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_context_builder.py
max_attempts: 3
---

## Goal
Implement: context selection + citation parsing. The tests written by T-worker-036t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
