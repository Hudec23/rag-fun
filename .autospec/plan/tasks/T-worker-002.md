---
id: T-worker-002
kind: impl
feature: F-embed
title: sample_indices
service: worker
depends_on:
- T-worker-002t
edit:
- services/worker/src/rag_worker/viz/sampling.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_viz_sampling.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/viz/sampling.py && uv run --frozen ruff check src/rag_worker/viz/sampling.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_sampling.py
max_attempts: 3
---

## Goal
Implement: sample_indices. The tests written by T-worker-002t define done.

## Context
Stub in `services/worker/src/rag_worker/viz/sampling.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def sample_indices(n: int, cap: int = 200) -> list[int]:
    """Evenly spaced indices: [round(x) for x in numpy.linspace(0, n-1, min(n, cap))] as ints,
    strictly increasing and unique. n = 0 -> []; n <= cap -> list(range(n))."""
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
