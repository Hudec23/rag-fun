---
id: T-api-002
kind: impl
feature: F-stage-flow
title: validate_stage_params cross-field rules
service: api
depends_on:
- T-api-002t
edit:
- services/api/src/rag_api/services/validation.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/unit/test_validation.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/validation.py && uv run --frozen ruff check src/rag_api/services/validation.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_validation.py
max_attempts: 3
---

## Goal
Implement: validate_stage_params cross-field rules. The tests written by T-api-002t define done.

## Context
Stub in `services/api/src/rag_api/services/validation.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any


def validate_stage_params(stage: str, params: dict[str, Any]) -> None:
    """Cross-field rules the JSON schema cannot express (api.yaml runChunk) -> VALIDATION_ERROR:
    chunk fixed/sentence/recursive: overlap >= length (details.field='params.overlap');
    chunk table: text_overlap >= text_length ('params.text_overlap');
    chunk semantic: min_sentences > max_sentences ('params.min_sentences').
    Every other stage/params: no-op."""
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
