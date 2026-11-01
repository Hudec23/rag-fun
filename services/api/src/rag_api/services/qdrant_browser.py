"""Qdrant browser endpoints: resolve the collection row (404 COLLECTION_NOT_FOUND), then delegate to
QdrantReader with row.qdrant_name. Reader errors other than 'collection missing' -> 503 QDRANT_ERROR."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.qdrant_read import QdrantReader
from rag_api.schemas.qdrant import (
    CountRequest,
    CountResponse,
    FacetResponse,
    QdrantInfo,
    QdrantPoint,
    ScrollRequest,
    ScrollResponse,
)


async def info(session: AsyncSession, q: QdrantReader, collection_id: str) -> QdrantInfo:
    raise NotImplementedError("not implemented")


async def scroll(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: ScrollRequest
) -> ScrollResponse:
    raise NotImplementedError("not implemented")


async def count(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: CountRequest
) -> CountResponse:
    raise NotImplementedError("not implemented")


async def facet(
    session: AsyncSession, q: QdrantReader, collection_id: str, key: str
) -> FacetResponse:
    raise NotImplementedError("not implemented")


async def get_point(
    session: AsyncSession, q: QdrantReader, collection_id: str, point_id: str
) -> QdrantPoint:
    raise NotImplementedError("not implemented")
