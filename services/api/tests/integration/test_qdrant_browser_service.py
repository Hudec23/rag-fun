"""Integration tests for rag_api.services.qdrant_browser: info, scroll, count, facet,
get_point. Real postgres via the `session` fixture; QdrantReader is replaced by a
recording stub (no real Qdrant). The service is still a stub — every test here is red
until T-api-021."""

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.errors import AppError
from rag_api.schemas.qdrant import (
    CountRequest,
    CountResponse,
    DenseInfo,
    FacetResponse,
    FacetValue,
    PayloadIndexInfo,
    PointVectors,
    QdrantInfo,
    QdrantPoint,
    ScrollRequest,
    ScrollResponse,
    SparseInfo,
    SparseVector,
)
from rag_api.services import qdrant_browser
from tests.conftest import add_collection

MISSING_COLLECTION = "019a4b2c-1d00-7b00-8000-0000000000ab"
POINT_ID = "f" * 32
OFFSET = "c" * 32

COUNT = 42

FACET = FacetResponse(key="tags", values=[FacetValue(value="hr", count=1)])
POINT = QdrantPoint(
    id=POINT_ID,
    payload={"meta": {"tags": ["hr"]}},
    vectors=PointVectors(
        dense=[0.5, 0.25], sparse=SparseVector(indices=[1, 5], values=[0.75, 0.25])
    ),
)
SCROLL = ScrollResponse(points=[POINT], next_offset=OFFSET)


def make_info(name: str) -> QdrantInfo:
    return QdrantInfo(
        qdrant_name=name,
        exists=True,
        status="green",
        points_count=3,
        dense=DenseInfo(name="text-dense", size=1024, distance="Cosine"),
        sparse=SparseInfo(name="text-sparse", modifier="idf"),
        payload_indexes=[PayloadIndexInfo(key="meta.tags", type="keyword", points=3)],
    )


class StubReader:
    """Stands in for QdrantReader: records (method, args) per call, returns fixed
    results, and raises `error` instead of returning when it is set."""

    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.error = error

    def _record(self, method: str, args: tuple[Any, ...]) -> None:
        self.calls.append((method, args))
        if self.error is not None:
            raise self.error

    async def info(self, qdrant_name: str) -> QdrantInfo:
        self._record("info", (qdrant_name,))
        return make_info(qdrant_name)

    async def scroll(
        self,
        qdrant_name: str,
        flt: PayloadFilter,
        limit: int,
        offset: str | None,
        with_vectors: bool,
    ) -> ScrollResponse:
        self._record("scroll", (qdrant_name, flt, limit, offset, with_vectors))
        return SCROLL

    async def count(self, qdrant_name: str, flt: PayloadFilter) -> int:
        self._record("count", (qdrant_name, flt))
        return COUNT

    async def facet(self, qdrant_name: str, key: str) -> FacetResponse:
        self._record("facet", (qdrant_name, key))
        return FACET

    async def get_point(self, qdrant_name: str, point_id: str) -> QdrantPoint:
        self._record("get_point", (qdrant_name, point_id))
        return POINT


async def test_info_unknown_collection_is_collection_not_found(session: AsyncSession) -> None:
    stub = StubReader()
    with pytest.raises(AppError) as exc:
        await qdrant_browser.info(session, stub, MISSING_COLLECTION)
    assert exc.value.code == "COLLECTION_NOT_FOUND"
    assert exc.value.details == {"collection_id": MISSING_COLLECTION}
    assert stub.calls == []


async def test_info_delegates_to_reader_with_qdrant_name(session: AsyncSession) -> None:
    row = await add_collection(session, "default")
    stub = StubReader()
    result = await qdrant_browser.info(session, stub, row.id)
    assert stub.calls == [("info", (row.qdrant_name,))]
    assert result == make_info(row.qdrant_name)


async def test_scroll_passes_filter_limit_offset_and_with_vectors(session: AsyncSession) -> None:
    row = await add_collection(session, "default")
    stub = StubReader()
    flt = PayloadFilter.model_validate({"must": [{"key": "tags", "match": {"any": ["hr"]}}]})
    body = ScrollRequest(filter=flt, limit=25, offset=OFFSET, with_vectors=True)
    result = await qdrant_browser.scroll(session, stub, row.id, body)
    assert stub.calls == [("scroll", (row.qdrant_name, flt, 25, OFFSET, True))]
    assert result == SCROLL


async def test_count_returns_count_response(session: AsyncSession) -> None:
    row = await add_collection(session, "default")
    stub = StubReader()
    flt = PayloadFilter()
    result = await qdrant_browser.count(session, stub, row.id, CountRequest(filter=flt))
    assert stub.calls == [("count", (row.qdrant_name, flt))]
    assert result == CountResponse(count=COUNT)


async def test_reader_generic_error_is_qdrant_error(session: AsyncSession) -> None:
    row = await add_collection(session, "default")
    stub = StubReader(error=RuntimeError("qdrant down"))
    with pytest.raises(AppError) as exc:
        await qdrant_browser.info(session, stub, row.id)
    assert exc.value.code == "QDRANT_ERROR"
    assert stub.calls == [("info", (row.qdrant_name,))]


async def test_reader_point_not_found_propagates_unchanged(session: AsyncSession) -> None:
    row = await add_collection(session, "default")
    err = AppError("POINT_NOT_FOUND", details={"point_id": POINT_ID})
    stub = StubReader(error=err)
    with pytest.raises(AppError) as exc:
        await qdrant_browser.get_point(session, stub, row.id, POINT_ID)
    assert exc.value is err
    assert exc.value.code == "POINT_NOT_FOUND"
    assert stub.calls == [("get_point", (row.qdrant_name, POINT_ID))]
