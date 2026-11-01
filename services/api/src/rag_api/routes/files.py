from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.session import get_session
from rag_api.deps import get_events, get_queue, get_store, settings_dep
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.s3 import ObjectStore
from rag_api.schemas.base import Id, Tag
from rag_api.schemas.files import (
    BatchList,
    BatchOut,
    BatchUpdate,
    BatchWithFiles,
    FileList,
    FileOut,
    FileUpdate,
    IncomingFile,
)
from rag_api.schemas.runs import BatchIngestRequest, IngestRunList
from rag_api.services import batches, files, ingest_runs, tags, uploads

router = APIRouter(tags=["files"])

Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


@router.post("/batches", response_model=BatchWithFiles, status_code=201)
async def upload_batch(
    files_: Annotated[list[UploadFile] | None, File(alias="files")] = None,
    name: Annotated[str | None, Form(min_length=1, max_length=200)] = None,
    tags_csv: Annotated[str | None, Form(alias="tags", max_length=2000)] = None,
    session: AsyncSession = Depends(get_session),
    store: ObjectStore = Depends(get_store),
    settings: Settings = Depends(settings_dep),
) -> BatchWithFiles:
    incoming = [IncomingFile(filename=f.filename or "", data=await f.read()) for f in files_ or []]
    return await uploads.upload_batch(
        session, store, settings, incoming, name, tags.parse_tags_csv(tags_csv)
    )


@router.get("/batches", response_model=BatchList)
async def list_batches(
    limit: Limit = 50, offset: Offset = 0, session: AsyncSession = Depends(get_session)
) -> BatchList:
    return await batches.list_batches(session, limit, offset)


@router.get("/batches/{batch_id}", response_model=BatchWithFiles)
async def get_batch(batch_id: Id, session: AsyncSession = Depends(get_session)) -> BatchWithFiles:
    return await batches.get_batch(session, batch_id)


@router.patch("/batches/{batch_id}", response_model=BatchOut)
async def update_batch(
    batch_id: Id, body: BatchUpdate, session: AsyncSession = Depends(get_session)
) -> BatchOut:
    return await batches.update_batch(session, batch_id, body)


@router.post("/batches/{batch_id}/ingest", response_model=IngestRunList, status_code=202)
async def ingest_batch(
    batch_id: Id,
    body: BatchIngestRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> IngestRunList:
    return await ingest_runs.ingest_batch(session, queue, events, batch_id, body)


@router.get("/files", response_model=FileList)
async def list_files(
    limit: Limit = 50,
    offset: Offset = 0,
    batch_id: Id | None = None,
    tag: Tag | None = None,
    mime: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> FileList:
    return await files.list_files(session, limit, offset, batch_id, tag, mime)


@router.get("/files/{file_id}", response_model=FileOut)
async def get_file(file_id: Id, session: AsyncSession = Depends(get_session)) -> FileOut:
    return await files.get_file(session, file_id)


@router.patch("/files/{file_id}", response_model=FileOut)
async def update_file(
    file_id: Id, body: FileUpdate, session: AsyncSession = Depends(get_session)
) -> FileOut:
    return await files.update_file(session, file_id, body)


@router.delete("/files/{file_id}", status_code=204)
async def delete_file(
    file_id: Id,
    session: AsyncSession = Depends(get_session),
    store: ObjectStore = Depends(get_store),
    queue: JobQueue = Depends(get_queue),
    settings: Settings = Depends(settings_dep),
) -> Response:
    await files.delete_file(session, store, queue, settings, file_id)
    return Response(status_code=204)


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: Id,
    session: AsyncSession = Depends(get_session),
    store: ObjectStore = Depends(get_store),
    settings: Settings = Depends(settings_dep),
) -> Response:
    data, mime, filename = await files.get_file_content(session, store, settings, file_id)
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
