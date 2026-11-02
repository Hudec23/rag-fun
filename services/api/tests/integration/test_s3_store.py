"""S3ObjectStore (aioboto3) against the s3-test (RustFS) container. Fresh bucket name per test."""

from uuid import uuid4

import pytest

from rag_api.config import Settings
from rag_api.errors import AppError
from rag_api.s3 import ObjectNotFound, S3ObjectStore


async def test_ensure_bucket_then_head_bucket(settings: Settings) -> None:
    bucket = "t-" + uuid4().hex[:8]
    store = S3ObjectStore(settings)
    await store.ensure_bucket(bucket)
    await store.head_bucket(bucket)
    await store.ensure_bucket(bucket)


async def test_put_then_get_bytes(settings: Settings) -> None:
    bucket = "t-" + uuid4().hex[:8]
    store = S3ObjectStore(settings)
    await store.ensure_bucket(bucket)
    await store.put_bytes(bucket, "a/b.txt", b"hello", "text/plain")
    assert await store.get_bytes(bucket, "a/b.txt") == b"hello"


async def test_get_missing_key_raises_object_not_found(settings: Settings) -> None:
    bucket = "t-" + uuid4().hex[:8]
    store = S3ObjectStore(settings)
    await store.ensure_bucket(bucket)
    with pytest.raises(ObjectNotFound):
        await store.get_bytes(bucket, "missing.txt")


async def test_delete_then_get_raises_and_missing_delete_is_ok(settings: Settings) -> None:
    bucket = "t-" + uuid4().hex[:8]
    store = S3ObjectStore(settings)
    await store.ensure_bucket(bucket)
    await store.put_bytes(bucket, "a/b.txt", b"hello", "text/plain")
    await store.delete(bucket, "a/b.txt")
    with pytest.raises(ObjectNotFound):
        await store.get_bytes(bucket, "a/b.txt")
    await store.delete(bucket, "missing.txt")


async def test_head_missing_bucket_raises_s3_error(settings: Settings) -> None:
    store = S3ObjectStore(settings)
    with pytest.raises(AppError) as exc_info:
        await store.head_bucket("no-such-bucket-" + uuid4().hex[:8])
    assert exc_info.value.code == "S3_ERROR"


async def test_unicode_key_roundtrip(settings: Settings) -> None:
    bucket = "t-" + uuid4().hex[:8]
    store = S3ObjectStore(settings)
    await store.ensure_bucket(bucket)
    key = "ünï/čo.pdf"
    await store.put_bytes(bucket, key, b"fake-pdf-bytes", "application/pdf")
    assert await store.get_bytes(bucket, key) == b"fake-pdf-bytes"
