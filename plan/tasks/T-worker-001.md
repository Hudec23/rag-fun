---
id: T-worker-001
kind: impl
feature: F-chunk
title: chunk_stats
service: worker
depends_on:
- T-worker-001t
edit:
- services/worker/src/rag_worker/viz/stats.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_viz_stats.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/viz/stats.py && uv run --frozen ruff check src/rag_worker/viz/stats.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_stats.py
max_attempts: 3
---

## Goal
Implement: chunk_stats. The tests written by T-worker-001t define done.

## Context
Stub in `services/worker/src/rag_worker/viz/stats.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any


def chunk_stats(char_counts: list[int]) -> dict[str, Any]:
    """chunk artifact 'stats': count, min_chars, max_chars, mean_chars (round 2), histogram =
    numpy.histogram(char_counts, bins=min(20, max(1, count))) with bin_edges rounded to 2 decimals.
    Empty list -> count 0, min/max/mean 0, bin_edges [], counts []."""
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
