---
id: T-api-001
kind: impl
feature: F-upload
title: tag helpers normalize_tags + parse_tags_csv
service: api
depends_on:
- T-api-001t
edit:
- services/api/src/rag_api/services/tags.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/unit/test_tags.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/tags.py && uv run --frozen ruff check src/rag_api/services/tags.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_tags.py
max_attempts: 3
---

## Goal
Implement: tag helpers normalize_tags + parse_tags_csv. The tests written by T-api-001t define done.

## Context
Stub in `services/api/src/rag_api/services/tags.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
TAG_PATTERN = r"^[a-z0-9][a-z0-9_.:-]*$"


def normalize_tags(tags: list[str]) -> list[str]:
    """Deduplicate and sort ascending. Tags are already pattern-validated by the DTO."""
    raise NotImplementedError("not implemented")

def parse_tags_csv(raw: str | None) -> list[str]:
    """'finance, q3,,Q3 ' -> ['finance', 'q3']: split on ',', strip, lowercase, drop empty, normalize.
    Any tag not matching TAG_PATTERN or longer than 64 chars, or more than 32 tags ->
    AppError('VALIDATION_ERROR', details={'field': 'tags'})."""
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
