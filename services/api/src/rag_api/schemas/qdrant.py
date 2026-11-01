from typing import Any, Literal

from pydantic import Field

from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.schemas.base import Model, PointId


class DenseInfo(Model):
    name: Literal["text-dense"]
    size: int
    distance: str


class SparseInfo(Model):
    name: Literal["text-sparse"]
    modifier: Literal["idf", "none"]


class PayloadIndexInfo(Model):
    key: str
    type: str
    points: int


class QdrantInfo(Model):
    qdrant_name: str
    exists: bool
    status: Literal["green", "yellow", "grey", "red"] | None
    points_count: int | None
    dense: DenseInfo | None
    sparse: SparseInfo | None
    payload_indexes: list[PayloadIndexInfo]


class ScrollRequest(Model):
    filter: PayloadFilter
    limit: int = Field(ge=1, le=100)
    offset: PointId | None
    with_vectors: bool


class SparseVector(Model):
    indices: list[int]
    values: list[float]


class PointVectors(Model):
    dense: list[float]
    sparse: SparseVector


class QdrantPoint(Model):
    id: PointId
    payload: dict[str, Any]  # contracts/qdrant/payload.schema.json
    vectors: PointVectors | None


class ScrollResponse(Model):
    points: list[QdrantPoint]
    next_offset: PointId | None


class CountRequest(Model):
    filter: PayloadFilter


class CountResponse(Model):
    count: int


class FacetValue(Model):
    value: str
    count: int


class FacetResponse(Model):
    key: str
    values: list[FacetValue]
