from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.session import get_session
from rag_api.deps import get_queue
from rag_api.queue import JobQueue
from rag_api.schemas.base import Id
from rag_api.schemas.collections import CollectionCreate, CollectionList, CollectionOut
from rag_api.services import collections as svc

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=CollectionList)
async def list_collections(session: AsyncSession = Depends(get_session)) -> CollectionList:
    return await svc.list_collections(session)


@router.post("", response_model=CollectionOut, status_code=201)
async def create_collection(
    body: CollectionCreate, session: AsyncSession = Depends(get_session)
) -> CollectionOut:
    return await svc.create_collection(session, body)


@router.get("/{collection_id}", response_model=CollectionOut)
async def get_collection(
    collection_id: Id, session: AsyncSession = Depends(get_session)
) -> CollectionOut:
    return await svc.get_collection(
        session, collection_id
    )  # raises AppError("COLLECTION_NOT_FOUND")


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: Id,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
) -> Response:
    await svc.delete_collection(session, queue, collection_id)
    return Response(status_code=204)
