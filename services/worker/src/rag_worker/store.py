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
