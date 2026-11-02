"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""

from typing import Any
from uuid import UUID

from qdrant_client import models

from rag_api.contracts_gen.shared.common_schema import (
    FilterCondition,
    MatchAnyCondition,
    PayloadFilter,
    RangeCondition,
)
from rag_api.errors import AppError
from rag_api.schemas.qdrant import (
    DenseInfo,
    FacetResponse,
    FacetValue,
    PayloadIndexInfo,
    PointVectors,
    QdrantInfo,
    QdrantPoint,
    ScrollResponse,
    SparseInfo,
    SparseVector,
)


def _to_field_condition(c: FilterCondition) -> Any:
    key = f"meta.{c.key}"
    if isinstance(c, RangeCondition):
        return models.FieldCondition(key=key, range=models.Range(gte=c.range.gte, lte=c.range.lte))
    if isinstance(c, MatchAnyCondition):
        return models.FieldCondition(key=key, match=models.MatchAny(any=c.match.any))
    return models.FieldCondition(key=key, match=models.MatchValue(value=c.match.value))


def to_qdrant_filter(f: PayloadFilter) -> Any:
    """PayloadFilter -> qdrant_client.models.Filter (None when the filter is empty).
    key 'tags' -> 'meta.tags'; match.value -> MatchValue; match.any -> MatchAny; range -> Range."""
    must = [_to_field_condition(c) for c in f.must or []]
    should = [_to_field_condition(c) for c in f.should or []]
    must_not = [_to_field_condition(c) for c in f.must_not or []]
    if not (must or should or must_not):
        return None
    return models.Filter(must=must or None, should=should or None, must_not=must_not or None)


def _to_point_id(raw: Any) -> str:
    """Qdrant returns point ids as UUIDs (dashed strings); PointId is 32 lowercase hex."""
    if isinstance(raw, UUID):
        return raw.hex
    return str(raw).replace("-", "")


def _to_vectors(vector: Any) -> PointVectors | None:
    if not vector:
        return None
    dense = vector.get("text-dense")
    sparse = vector.get("text-sparse")
    if dense is None or sparse is None:
        return None
    return PointVectors(
        dense=[float(v) for v in dense],
        sparse=SparseVector(
            indices=[int(i) for i in sparse.indices], values=[float(v) for v in sparse.values]
        ),
    )


def _dense_info(params: Any) -> DenseInfo | None:
    vectors = getattr(params, "vectors", None)
    if isinstance(vectors, dict):
        entry = vectors.get("text-dense")
        if entry is not None:
            return DenseInfo(name="text-dense", size=entry.size, distance=str(entry.distance))
    return None


def _sparse_info(params: Any) -> SparseInfo | None:
    sparse_vectors = getattr(params, "sparse_vectors", None)
    if isinstance(sparse_vectors, dict):
        entry = sparse_vectors.get("text-sparse")
        if entry is not None:
            modifier = entry.modifier
            return SparseInfo(
                name="text-sparse", modifier="none" if modifier is None else str(modifier)
            )
    return None


class QdrantReader:
    def __init__(self, client: Any) -> None:
        self.client = client  # qdrant_client.AsyncQdrantClient

    async def info(self, qdrant_name: str) -> QdrantInfo:
        if not await self.client.collection_exists(qdrant_name):
            return QdrantInfo(
                qdrant_name=qdrant_name,
                exists=False,
                status=None,
                points_count=None,
                dense=None,
                sparse=None,
                payload_indexes=[],
            )
        ci = await self.client.get_collection(qdrant_name)
        payload_indexes = [
            PayloadIndexInfo(key=key, type=str(meta.data_type), points=int(meta.points))
            for key, meta in (ci.payload_schema or {}).items()
        ]
        return QdrantInfo(
            qdrant_name=qdrant_name,
            exists=True,
            status=ci.status.value if ci.status is not None else None,
            points_count=ci.points_count,
            dense=_dense_info(ci.config.params),
            sparse=_sparse_info(ci.config.params),
            payload_indexes=payload_indexes,
        )

    async def scroll(
        self,
        qdrant_name: str,
        flt: PayloadFilter,
        limit: int,
        offset: str | None,
        with_vectors: bool,
    ) -> ScrollResponse:
        records, next_offset = await self.client.scroll(
            qdrant_name,
            scroll_filter=to_qdrant_filter(flt),
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=with_vectors,
        )
        points = [
            QdrantPoint(
                id=_to_point_id(record.id),
                payload=record.payload or {},
                vectors=_to_vectors(record.vector) if with_vectors else None,
            )
            for record in records
        ]
        return ScrollResponse(
            points=points,
            next_offset=_to_point_id(next_offset) if next_offset is not None else None,
        )

    async def count(self, qdrant_name: str, flt: PayloadFilter) -> int:
        if not await self.client.collection_exists(qdrant_name):
            return 0
        result = await self.client.count(qdrant_name, count_filter=to_qdrant_filter(flt))
        return int(result.count)

    async def facet(self, qdrant_name: str, key: str) -> FacetResponse:
        result = await self.client.facet(qdrant_name, key=f"meta.{key}", limit=1000)
        values = [FacetValue(value=str(hit.value), count=hit.count) for hit in result.hits]
        values.sort(key=lambda v: (-v.count, v.value))
        return FacetResponse(key=key, values=values)

    async def get_point(self, qdrant_name: str, point_id: str) -> QdrantPoint:
        records = await self.client.retrieve(
            qdrant_name, ids=[point_id], with_payload=True, with_vectors=False
        )
        if not records:
            raise AppError("POINT_NOT_FOUND", details={"point_id": point_id})
        record = records[0]
        return QdrantPoint(id=_to_point_id(record.id), payload=record.payload or {}, vectors=None)
