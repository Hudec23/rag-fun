---
id: T-worker-013
kind: impl
feature: F-parse
title: assign_spans (full_text + char spans)
service: worker
depends_on:
- T-worker-013t
edit:
- services/worker/src/rag_worker/components/text_layout.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_text_layout.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/text_layout.py && uv run --frozen ruff check src/rag_worker/components/text_layout.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_text_layout.py
max_attempts: 3
---

## Goal
Implement: assign_spans (full_text + char spans). The tests written by T-worker-013t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
