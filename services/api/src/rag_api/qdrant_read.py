"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""

from typing import Any

from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.schemas.qdrant import FacetResponse, QdrantInfo, QdrantPoint, ScrollResponse


def to_qdrant_filter(f: PayloadFilter) -> Any:
    """PayloadFilter -> qdrant_client.models.Filter (None when the filter is empty).
    key 'tags' -> 'meta.tags'; match.value -> MatchValue; match.any -> MatchAny; range -> Range."""
    raise NotImplementedError("not implemented")


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
