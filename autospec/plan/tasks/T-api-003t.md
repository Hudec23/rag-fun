---
id: T-api-003t
kind: test
feature: F-upload
title: 'Write tests: S3ObjectStore (aioboto3 against RustFS)'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_s3_store.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_s3_store.py && uv run --frozen ruff check tests/integration/test_s3_store.py && uv run --frozen pytest -q --collect-only tests/integration/test_s3_store.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_s3_store.py
max_attempts: 3
---

## Goal
Write unit tests for: S3ObjectStore (aioboto3 against RustFS). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-003 implements it.

## Context
Integration test against s3-test (S3_ENDPOINT_URL). Use a fresh bucket name per test (e.g. 't-' + uuid4().hex[:8]). Use the `settings` fixture.

Stub in `services/api/src/rag_api/s3.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""S3 (RustFS) access. Buckets: uploads (api writes), artifacts (api reads only)."""
from typing import Protocol
from rag_api.config import Settings


class ObjectStore(Protocol):
    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
    async def get_bytes(self, bucket: str, key: str) -> bytes: ...
    async def delete(self, bucket: str, key: str) -> None: ...
    async def ensure_bucket(self, bucket: str) -> None: ...
    async def head_bucket(self, bucket: str) -> None: ...

class ObjectNotFound(Exception):
    """Raised by get_bytes when the key does not exist."""

class S3ObjectStore:
    """aioboto3 implementation. Every boto/network failure is raised as AppError("S3_ERROR"),
    a missing key in get_bytes as ObjectNotFound."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError("not implemented")

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        raise NotImplementedError("not implemented")

    async def delete(self, bucket: str, key: str) -> None:
        raise NotImplementedError("not implemented")

    async def ensure_bucket(self, bucket: str) -> None:
        raise NotImplementedError("not implemented")

    async def head_bucket(self, bucket: str) -> None:
        raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. S3ObjectStore(settings).ensure_bucket('t-<random hex>') then head_bucket(same) succeeds; ensure_bucket twice does not raise
2. put_bytes(bucket, 'a/b.txt', b'hello', 'text/plain') then get_bytes == b'hello'
3. get_bytes(bucket, 'missing.txt') raises ObjectNotFound
4. delete(bucket, 'a/b.txt') then get_bytes raises ObjectNotFound; deleting a missing key does not raise
5. head_bucket('no-such-bucket-<hex>') raises AppError with code S3_ERROR
6. keys with unicode 'ünï/čo.pdf' round-trip

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
