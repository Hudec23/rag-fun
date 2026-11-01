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
