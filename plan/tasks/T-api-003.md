---
id: T-api-003
kind: impl
feature: F-upload
title: S3ObjectStore (aioboto3 against RustFS)
service: api
depends_on:
- T-api-003t
edit:
- services/api/src/rag_api/s3.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_s3_store.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/s3.py && uv run --frozen ruff check src/rag_api/s3.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_s3_store.py
max_attempts: 3
---

## Goal
Implement: S3ObjectStore (aioboto3 against RustFS). The tests written by T-api-003t define done.

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

## Steps
1. aioboto3.Session().client('s3', endpoint_url=settings.s3_endpoint_url, aws_access_key_id=…, aws_secret_access_key=…, region_name='us-east-1') as an async context manager per call.
2. Map botocore ClientError code NoSuchKey/404 in get_bytes to ObjectNotFound; every other ClientError/EndpointConnectionError to AppError('S3_ERROR', details={'bucket': bucket}).
3. ensure_bucket: head_bucket, create_bucket on 404.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
