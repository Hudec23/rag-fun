---
id: T-api-001t
kind: test
feature: F-upload
title: 'Write tests: tag helpers normalize_tags + parse_tags_csv'
service: api
depends_on: []
edit:
- services/api/tests/unit/test_tags.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_tags.py && uv run --frozen ruff check tests/unit/test_tags.py && uv run --frozen pytest -q --collect-only tests/unit/test_tags.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_tags.py
max_attempts: 3
---

## Goal
Write unit tests for: tag helpers normalize_tags + parse_tags_csv. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-001 implements it.

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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. normalize_tags(['b', 'a', 'b']) == ['a', 'b']
2. normalize_tags([]) == []
3. parse_tags_csv('finance, q3,,Q3 ') == ['finance', 'q3']
4. parse_tags_csv(None) == [] and parse_tags_csv('') == []
5. parse_tags_csv('ok,Bad Tag!') raises AppError code VALIDATION_ERROR with details == {'field': 'tags'}
6. parse_tags_csv('a'*65) raises VALIDATION_ERROR
7. parse_tags_csv(','.join(f't{i}' for i in range(33))) raises VALIDATION_ERROR (33 > 32 tags)
8. parse_tags_csv('v1.2:beta_x-y') == ['v1.2:beta_x-y'] (all allowed characters)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
