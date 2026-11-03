---
id: T-api-002t
kind: test
feature: F-stage-flow
title: 'Write tests: validate_stage_params cross-field rules'
service: api
depends_on: []
edit:
- services/api/tests/unit/test_validation.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_validation.py && uv run --frozen ruff check tests/unit/test_validation.py && uv run --frozen pytest -q --collect-only tests/unit/test_validation.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_validation.py
max_attempts: 3
---

## Goal
Write unit tests for: validate_stage_params cross-field rules. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-002 implements it.

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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. chunk fixed length 10 overlap 9 → no error (returns None)
2. chunk fixed length 10 overlap 10 → AppError VALIDATION_ERROR details {'field': 'params.overlap'}
3. chunk sentence length 2 overlap 3 → VALIDATION_ERROR field params.overlap
4. chunk recursive length 100 overlap 100 → VALIDATION_ERROR field params.overlap
5. chunk table text_length 50 text_overlap 50 → VALIDATION_ERROR field params.text_overlap
6. chunk semantic min_sentences 5 max_sentences 4 → VALIDATION_ERROR field params.min_sentences; min 4 max 4 → ok
7. chunk structure {'strategy': 'structure', 'max_tokens': 64, 'merge_peers': True} → ok
8. stage 'parse' and 'embed' with any params → ok

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
