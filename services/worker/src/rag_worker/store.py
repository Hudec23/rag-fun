"""S3 access: read uploads (originals) and artifacts, write artifacts only."""

import json
from typing import Any, Protocol

import aioboto3
from aiobotocore.client import AioBaseClient
from botocore.exceptions import ClientError, EndpointConnectionError

from rag_worker.config import Settings
from rag_worker.errors import WorkerError


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

    def _missing_error(self, bucket: str, key: str) -> WorkerError:
        if bucket == self.settings.s3_bucket_artifacts:
            code = "ARTIFACT_NOT_FOUND"
        elif bucket == self.settings.s3_bucket_uploads:
            code = "FILE_NOT_FOUND"
        else:
            code = "S3_ERROR"
        return WorkerError(code, details={"key": key})

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        try:
            async with self._client() as client:
                resp = await client.get_object(Bucket=bucket, Key=key)
                return await resp["Body"].read()
        except ClientError as e:
            if self._is_missing(e):
                raise self._missing_error(bucket, key) from e
            raise WorkerError("S3_ERROR", details={"key": key}) from e
        except EndpointConnectionError as e:
            raise WorkerError("S3_ERROR", details={"key": key}) from e

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        try:
            async with self._client() as client:
                await client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        except ClientError as e:
            raise WorkerError("S3_ERROR", details={"key": key}) from e
        except EndpointConnectionError as e:
            raise WorkerError("S3_ERROR", details={"key": key}) from e

    async def get_json(self, bucket: str, key: str) -> Any:
        return json.loads(await self.get_bytes(bucket, key))

    async def put_json(self, bucket: str, key: str, obj: Any) -> None:
        data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        await self.put_bytes(bucket, key, data, "application/json")
