---
id: T-worker-005t
kind: test
feature: F-stage-flow
title: 'Write tests: S3ObjectStore for artifacts'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_store_s3.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_store_s3.py && uv run --frozen ruff check tests/integration/test_store_s3.py && uv run --frozen pytest -q --collect-only tests/integration/test_store_s3.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_store_s3.py
max_attempts: 3
---

## Goal
Write unit tests for: S3ObjectStore for artifacts. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-005 implements it.

## Context
Integration test against s3-test (S3_* env). Create buckets 'uploads' and 'artifacts' at test start with aioboto3 if missing.

Stub in `services/worker/src/rag_worker/store.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""S3 access: read uploads (originals) and artifacts, write artifacts only."""
from typing import Any, Protocol
from rag_worker.config import Settings


class ObjectStore(Protocol):
    async def get_bytes(self, bucket: str, key: str) -> bytes: ...
    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
    async def get_json(self, bucket: str, key: str) -> Any: ...
    async def put_json(self, bucket: str, key: str, obj: Any) -> None: ...

class S3ObjectStore:
    """aioboto3. Missing key -> WorkerError('ARTIFACT_NOT_FOUND' for bucket artifacts,
    'FILE_NOT_FOUND' for bucket uploads, details={'key': key}); any other failure ->
    WorkerError('S3_ERROR', details={'key': key}). put_json: UTF-8, separators (',', ':'),
    content type application/json; ensure_ascii False."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        raise NotImplementedError("not implemented")

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError("not implemented")

    async def get_json(self, bucket: str, key: str) -> Any:
        raise NotImplementedError("not implemented")

    async def put_json(self, bucket: str, key: str, obj: Any) -> None:
        raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. put_json('artifacts', 'r/chunk/v1.json', {'a': 'ü'}) then get_json → {'a': 'ü'}; raw bytes == b'{"a":"\xc3\xbc"}' (compact, UTF-8)
2. put_bytes/get_bytes round-trip of PNG bytes
3. get_bytes missing key in bucket 'artifacts' → WorkerError ARTIFACT_NOT_FOUND details {'key': key}
4. get_bytes missing key in bucket 'uploads' → WorkerError FILE_NOT_FOUND
5. bucket that does not exist → WorkerError S3_ERROR

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
