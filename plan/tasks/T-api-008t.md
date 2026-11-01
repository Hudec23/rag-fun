---
id: T-api-008t
kind: test
feature: F-upload
title: 'Write tests: upload_batch + detect_mime + default_batch_name'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_uploads.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_uploads.py && uv run --frozen ruff check tests/integration/test_uploads.py && uv run --frozen pytest -q --collect-only tests/integration/test_uploads.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_uploads.py
max_attempts: 3
---

## Goal
Write unit tests for: upload_batch + detect_mime + default_batch_name. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-008 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/uploads.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Batch upload (R-001, R-002, R-003)."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import BatchWithFiles, IncomingFile


def detect_mime(filename: str) -> str:
    """MIME from the lowercase extension via catalog.MIME_BY_EXT.
    Unknown/missing extension -> AppError('UNSUPPORTED_FILE_TYPE', details={'filename': filename})."""
    raise NotImplementedError("not implemented")

def default_batch_name(now_iso: str) -> str:
    """'2026-11-01T18:22:05.123Z' -> 'Batch 2026-11-01 18:22'."""
    raise NotImplementedError("not implemented")

async def upload_batch(
    session: AsyncSession,
    store: ObjectStore,
    settings: Settings,
    files: list[IncomingFile],
    name: str | None,
    tags: list[str],
) -> BatchWithFiles:
    """Validate ALL files first, in this order, before storing anything:
    0 files -> EMPTY_UPLOAD; len > settings.max_files_per_batch -> TOO_MANY_FILES (details.limit);
    for each file in order: detect_mime (UNSUPPORTED_FILE_TYPE); len(data) > max_upload_mb*1024*1024
    -> FILE_TOO_LARGE (details.filename, details.limit_mb); len(data) == 0 -> VALIDATION_ERROR
    (details.field='files', details.filename).
    Then: insert batch (name or default_batch_name, tags normalized), for each file: id=new_id(),
    key f'{batch_id}/{file_id}/{filename}', store.put_bytes(settings.s3_bucket_uploads, key, data, mime),
    sha256 hex of data, insert files row (tags []). Flush. Return BatchWithFiles (files in upload order,
    batch.file_count = len(files))."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. detect_mime('Report.PDF') == 'application/pdf'; 'a.jpeg' → 'image/jpeg'; 'x.tif' → 'image/tiff'
2. detect_mime('notes.rtf') and detect_mime('README') raise AppError UNSUPPORTED_FILE_TYPE with details {'filename': …}
3. default_batch_name('2026-11-01T18:22:05.123Z') == 'Batch 2026-11-01 18:22'
4. upload_batch with 2 files (a.md, b.pdf), name None, tags ['x'] (frozen_now) → batch.name 'Batch 2026-11-01 18:22', tags ['x'], file_count 2; files in order with sha256 hex of each payload; store.objects has keys f'{batch_id}/{file_id}/a.md' in bucket 'uploads' with content type 'text/markdown'
5. 0 files → EMPTY_UPLOAD; 21 files (max_files_per_batch 20) → TOO_MANY_FILES details {'limit': 20}
6. second file > max_upload_mb (monkeypatch settings.max_upload_mb = 0 makes 1 byte too large) → FILE_TOO_LARGE details {'filename': 'b.pdf', 'limit_mb': 0} and store.objects is empty, no batch row
7. one unsupported extension among valid files → UNSUPPORTED_FILE_TYPE and nothing stored
8. empty file (0 bytes) → VALIDATION_ERROR details {'field': 'files', 'filename': …}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
