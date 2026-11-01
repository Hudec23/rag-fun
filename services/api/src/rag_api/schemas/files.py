from typing import Annotated

from pydantic import Field

from rag_api.schemas.base import Id, Model, PageInfo, Tags, Timestamp


class BatchOut(Model):
    id: Id
    name: str
    tags: list[str]
    file_count: int
    created_at: Timestamp


class BatchUpdate(Model):
    name: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    tags: Tags | None = None


class FileOut(Model):
    id: Id
    batch_id: Id
    filename: str
    mime: str
    size_bytes: int
    sha256: str
    tags: list[str]
    created_at: Timestamp


class FileUpdate(Model):
    tags: Tags


class BatchWithFiles(Model):
    batch: BatchOut
    files: list[FileOut]


class BatchList(Model):
    items: list[BatchOut]
    page: PageInfo


class FileList(Model):
    items: list[FileOut]
    page: PageInfo


class IncomingFile(Model):
    """One uploaded file as read by the route (bytes already in memory)."""

    filename: str
    data: bytes
