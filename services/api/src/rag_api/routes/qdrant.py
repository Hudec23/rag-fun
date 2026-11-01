from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.session import get_session
from rag_api.deps import get_qdrant
from rag_api.qdrant_read import QdrantReader
from rag_api.schemas.base import Id, PointId
from rag_api.schemas.qdrant import (
    CountRequest,
    CountResponse,
    FacetResponse,
    QdrantInfo,
    QdrantPoint,
    ScrollRequest,
    ScrollResponse,
)
from rag_api.services import qdrant_browser

router = APIRouter(prefix="/collections/{collection_id}/qdrant", tags=["qdrant"])

FacetKey = Literal[
    "file_id", "batch_id", "tags", "mime", "element_type", "chunk_strategy", "parse_strategy"
]


@router.get("", response_model=QdrantInfo)
async def info(
    collection_id: Id,
    session: AsyncSession = Depends(get_session),
    q: QdrantReader = Depends(get_qdrant),
) -> QdrantInfo:
    return await qdrant_browser.info(session, q, collection_id)


@router.post("/scroll", response_model=ScrollResponse)
async def scroll(
    collection_id: Id,
    body: ScrollRequest,
    session: AsyncSession = Depends(get_session),
    q: QdrantReader = Depends(get_qdrant),
) -> ScrollResponse:
    return await qdrant_browser.scroll(session, q, collection_id, body)


@router.post("/count", response_model=CountResponse)
async def count(
    collection_id: Id,
    body: CountRequest,
    session: AsyncSession = Depends(get_session),
    q: QdrantReader = Depends(get_qdrant),
) -> CountResponse:
    return await qdrant_browser.count(session, q, collection_id, body)


@router.get("/facets/{key}", response_model=FacetResponse)
async def facet(
    collection_id: Id,
    key: FacetKey,
    session: AsyncSession = Depends(get_session),
    q: QdrantReader = Depends(get_qdrant),
) -> FacetResponse:
    return await qdrant_browser.facet(session, q, collection_id, key)


@router.get("/points/{point_id}", response_model=QdrantPoint)
async def point(
    collection_id: Id,
    point_id: PointId,
    session: AsyncSession = Depends(get_session),
    q: QdrantReader = Depends(get_qdrant),
) -> QdrantPoint:
    return await qdrant_browser.get_point(session, q, collection_id, point_id)
