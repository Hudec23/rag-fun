"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""

from typing import Any

from qdrant_client import models

from rag_api.contracts_gen.shared.common_schema import (
    FilterCondition,
    MatchAnyCondition,
    PayloadFilter,
    RangeCondition,
)
from rag_api.schemas.qdrant import FacetResponse, QdrantInfo, QdrantPoint, ScrollResponse


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


class QdrantReader:
    def __init__(self, client: Any) -> None:
        self.client = client  # qdrant_client.AsyncQdrantClient

    async def info(self, qdrant_name: str) -> QdrantInfo:
        raise NotImplementedError("not implemented")

    async def scroll(
        self,
        qdrant_name: str,
        flt: PayloadFilter,
        limit: int,
        offset: str | None,
        with_vectors: bool,
    ) -> ScrollResponse:
        raise NotImplementedError("not implemented")

    async def count(self, qdrant_name: str, flt: PayloadFilter) -> int:
        raise NotImplementedError("not implemented")

    async def facet(self, qdrant_name: str, key: str) -> FacetResponse:
        raise NotImplementedError("not implemented")

    async def get_point(self, qdrant_name: str, point_id: str) -> QdrantPoint:
        raise NotImplementedError("not implemented")
