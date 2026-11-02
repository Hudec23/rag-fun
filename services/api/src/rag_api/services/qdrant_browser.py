"""Qdrant browser endpoints: resolve the collection row (404 COLLECTION_NOT_FOUND), then delegate to
QdrantReader with row.qdrant_name. Reader errors other than 'collection missing' -> 503 QDRANT_ERROR."""

from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.errors import AppError
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
from rag_api.services.collections import load_collection


def _collection_missing(e: Exception) -> bool:
    """True when the qdrant client reports a missing collection (404 whose body says 'doesn't exist')."""
    return (
        isinstance(e, UnexpectedResponse) and e.status_code == 404 and b"doesn't exist" in e.content
    )


async def info(session: AsyncSession, q: QdrantReader, collection_id: str) -> QdrantInfo:
    """The reader already returns exists=False for a missing collection; only wrap foreign errors."""
    row = await load_collection(session, collection_id)
    try:
        return await q.info(row.qdrant_name)
    except AppError:
        raise
    except Exception as e:
        raise AppError("QDRANT_ERROR") from e


async def scroll(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: ScrollRequest
) -> ScrollResponse:
    row = await load_collection(session, collection_id)
    try:
        return await q.scroll(
            row.qdrant_name, body.filter, body.limit, body.offset, body.with_vectors
        )
    except AppError:
        raise
    except Exception as e:
        if _collection_missing(e):
            return ScrollResponse(points=[], next_offset=None)
        raise AppError("QDRANT_ERROR") from e


async def count(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: CountRequest
) -> CountResponse:
    """The reader already returns 0 for a missing collection; only wrap foreign errors."""
    row = await load_collection(session, collection_id)
    try:
        n = await q.count(row.qdrant_name, body.filter)
    except AppError:
        raise
    except Exception as e:
        raise AppError("QDRANT_ERROR") from e
    return CountResponse(count=n)


async def facet(
    session: AsyncSession, q: QdrantReader, collection_id: str, key: str
) -> FacetResponse:
    row = await load_collection(session, collection_id)
    try:
        return await q.facet(row.qdrant_name, key)
    except AppError:
        raise
    except Exception as e:
        if _collection_missing(e):
            return FacetResponse(key=key, values=[])
        raise AppError("QDRANT_ERROR") from e


async def get_point(
    session: AsyncSession, q: QdrantReader, collection_id: str, point_id: str
) -> QdrantPoint:
    row = await load_collection(session, collection_id)
    try:
        return await q.get_point(row.qdrant_name, point_id)
    except AppError:
        raise
    except Exception as e:
        if _collection_missing(e):
            raise AppError("POINT_NOT_FOUND", details={"point_id": point_id}) from e
        raise AppError("QDRANT_ERROR") from e
