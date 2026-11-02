"""S3 (RustFS) access. Buckets: uploads (api writes), artifacts (api reads only)."""

from typing import Protocol

import aioboto3
from aiobotocore.client import AioBaseClient
from botocore.exceptions import ClientError, EndpointConnectionError

from rag_api.config import Settings
from rag_api.errors import AppError


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

    def _client(self) -> AioBaseClient:
        return aioboto3.Session().client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key,
            aws_secret_access_key=self.settings.s3_secret_key,
            region_name="us-east-1",
        )

    @staticmethod
    def _is_missing(e: ClientError) -> bool:
        code = e.response.get("Error", {}).get("Code")
        status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        return code in ("NoSuchKey", "404") or status == 404

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        try:
            async with self._client() as client:
                await client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        except ClientError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
        except EndpointConnectionError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        try:
            async with self._client() as client:
                resp = await client.get_object(Bucket=bucket, Key=key)
                return await resp["Body"].read()
        except ClientError as e:
            if self._is_missing(e):
                raise ObjectNotFound from e
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
        except EndpointConnectionError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e

    async def delete(self, bucket: str, key: str) -> None:
        try:
            async with self._client() as client:
                await client.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
        except EndpointConnectionError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e

    async def ensure_bucket(self, bucket: str) -> None:
        try:
            async with self._client() as client:
                try:
                    await client.head_bucket(Bucket=bucket)
                    return
                except ClientError as e:
                    if not self._is_missing(e):
                        raise
                    await client.create_bucket(Bucket=bucket)
        except ClientError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
        except EndpointConnectionError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e

    async def head_bucket(self, bucket: str) -> None:
        try:
            async with self._client() as client:
                await client.head_bucket(Bucket=bucket)
        except ClientError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
        except EndpointConnectionError as e:
            raise AppError("S3_ERROR", details={"bucket": bucket}) from e
