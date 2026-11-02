"""S3ObjectStore (aioboto3) against the s3-test (RustFS) container. Buckets 'uploads' and
'artifacts' are ensured at test start."""

from collections.abc import AsyncIterator
from typing import Any

import aioboto3
import pytest
from botocore.exceptions import ClientError

from rag_worker.config import get_settings
from rag_worker.errors import WorkerError
from rag_worker.store import S3ObjectStore
from tests.conftest import SAMPLES


@pytest.fixture(scope="module", autouse=True)
async def s3_buckets() -> AsyncIterator[None]:
    settings = get_settings()
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    ) as client:
        for bucket in (settings.s3_bucket_uploads, settings.s3_bucket_artifacts):
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError:
                await client.create_bucket(Bucket=bucket)
    yield


@pytest.fixture
def store(ctx: dict[str, Any]) -> S3ObjectStore:
    return S3ObjectStore(ctx["settings"])


async def test_put_json_then_get_json_compact_utf8(store: S3ObjectStore) -> None:
    await store.put_json("artifacts", "r/chunk/v1.json", {"a": "ü"})
    assert await store.get_json("artifacts", "r/chunk/v1.json") == {"a": "ü"}
    assert await store.get_bytes("artifacts", "r/chunk/v1.json") == b'{"a":"\xc3\xbc"}'


async def test_put_then_get_bytes_roundtrip_png(store: S3ObjectStore) -> None:
    data = (SAMPLES / "scan-invoice.png").read_bytes()
    await store.put_bytes("artifacts", "r/scan/scan-invoice.png", data, "image/png")
    assert await store.get_bytes("artifacts", "r/scan/scan-invoice.png") == data


async def test_get_bytes_missing_artifact_raises_artifact_not_found(store: S3ObjectStore) -> None:
    with pytest.raises(WorkerError) as exc_info:
        await store.get_bytes("artifacts", "missing/chunk/v1.json")
    assert exc_info.value.code == "ARTIFACT_NOT_FOUND"
    assert exc_info.value.details == {"key": "missing/chunk/v1.json"}


async def test_get_bytes_missing_upload_raises_file_not_found(store: S3ObjectStore) -> None:
    with pytest.raises(WorkerError) as exc_info:
        await store.get_bytes("uploads", "f-0001/scan-invoice.png")
    assert exc_info.value.code == "FILE_NOT_FOUND"
    assert exc_info.value.details == {"key": "f-0001/scan-invoice.png"}


async def test_get_bytes_missing_bucket_raises_s3_error(store: S3ObjectStore) -> None:
    with pytest.raises(WorkerError) as exc_info:
        await store.get_bytes("no-such-bucket", "r/chunk/v1.json")
    assert exc_info.value.code == "S3_ERROR"
    assert exc_info.value.details == {"key": "r/chunk/v1.json"}
