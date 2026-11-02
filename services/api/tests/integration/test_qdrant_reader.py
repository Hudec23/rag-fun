"""QdrantReader (rag_api.qdrant_read) against the qdrant-test container:
fresh 'rf_<32 hex>' collection per seeded test, deleted in teardown."""

import json
from collections.abc import AsyncIterator
from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from qdrant_client import AsyncQdrantClient, models

from rag_api.config import Settings
from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.errors import AppError
from rag_api.qdrant_read import QdrantReader
from rag_api.schemas.qdrant import (
    DenseInfo,
    FacetResponse,
    FacetValue,
    QdrantInfo,
    SparseInfo,
)
from tests.conftest import FIXTURES
from tests.contract import errors

Seed = tuple[str, list[str], list[dict[str, Any]]]

DENSE = [0.5, 0.25, -0.5, 0.125]
SPARSE = {"indices": [1, 5, 9], "values": [0.75, 0.5, 0.25]}
TAGS = (["hr"], ["hr"], ["tax"])


@pytest.fixture
async def qdrant_client(settings: Settings) -> AsyncIterator[AsyncQdrantClient]:
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def reader(qdrant_client: AsyncQdrantClient) -> QdrantReader:
    return QdrantReader(qdrant_client)


@pytest.fixture
async def seeded(qdrant_client: AsyncQdrantClient) -> AsyncIterator[Seed]:
    name = "rf_" + uuid4().hex
    await qdrant_client.create_collection(
        name,
        vectors_config={"text-dense": models.VectorParams(size=4, distance=models.Distance.COSINE)},
        sparse_vectors_config={
            "text-sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    await qdrant_client.create_payload_index(
        name, "meta.tags", field_schema=models.PayloadSchemaType.KEYWORD
    )
    template = json.loads((FIXTURES / "qdrant__payload.json").read_text())
    payloads: list[dict[str, Any]] = []
    for tags in TAGS:
        payload = deepcopy(template)
        payload["meta"]["tags"] = tags
        assert errors(payload, "qdrant/payload.schema.json") == []
        payloads.append(payload)
    point_ids = [uuid4().hex for _ in payloads]
    for pid, payload in zip(point_ids, payloads, strict=True):
        await qdrant_client.upsert(
            name,
            [
                models.PointStruct(
                    id=pid,
                    vector={"text-dense": DENSE, "text-sparse": SPARSE},
                    payload=payload,
                )
            ],
        )
    yield name, point_ids, payloads
    await qdrant_client.delete_collection(name)


async def test_info_on_missing_collection(reader: QdrantReader) -> None:
    name = "rf_" + uuid4().hex
    assert await reader.info(name) == QdrantInfo(
        qdrant_name=name,
        exists=False,
        status=None,
        points_count=None,
        dense=None,
        sparse=None,
        payload_indexes=[],
    )


async def test_info_on_seeded_collection(reader: QdrantReader, seeded: Seed) -> None:
    name, _, _ = seeded
    info = await reader.info(name)
    assert info.exists is True
    assert info.points_count == 3
    assert info.dense == DenseInfo(name="text-dense", size=4, distance="Cosine")
    assert info.sparse == SparseInfo(name="text-sparse", modifier="idf")
    assert {(i.key, i.type) for i in info.payload_indexes} == {("meta.tags", "keyword")}


async def test_scroll_pages_with_filter(reader: QdrantReader, seeded: Seed) -> None:
    name, point_ids, payloads = seeded
    flt = PayloadFilter.model_validate({"must": [{"key": "tags", "match": {"any": ["hr"]}}]})
    first = await reader.scroll(name, flt, limit=1, offset=None, with_vectors=False)
    assert len(first.points) == 1
    assert first.points[0].vectors is None
    assert first.next_offset is not None
    second = await reader.scroll(name, flt, limit=1, offset=first.next_offset, with_vectors=False)
    assert len(second.points) == 1
    assert second.points[0].vectors is None
    assert second.next_offset is None
    assert {first.points[0].id, second.points[0].id} == set(point_ids[:2])
    # points 0 and 1 carry identical payloads (same template, tags ['hr']); dicts are unhashable
    assert [first.points[0].payload, second.points[0].payload] == [payloads[0], payloads[1]]


async def test_scroll_with_vectors(reader: QdrantReader, seeded: Seed) -> None:
    name, point_ids, _ = seeded
    resp = await reader.scroll(name, PayloadFilter(), limit=3, offset=None, with_vectors=True)
    assert {p.id for p in resp.points} == set(point_ids)
    assert resp.next_offset is None
    for point in resp.points:
        assert point.vectors is not None
        assert len(point.vectors.dense) == 4
        assert all(isinstance(v, float) for v in point.vectors.dense)
        assert len(point.vectors.sparse.indices) > 0
        assert len(point.vectors.sparse.values) == len(point.vectors.sparse.indices)


async def test_count_with_and_without_filter(reader: QdrantReader, seeded: Seed) -> None:
    name, _, _ = seeded
    assert await reader.count(name, PayloadFilter()) == 3
    tax = PayloadFilter.model_validate({"must": [{"key": "tags", "match": {"any": ["tax"]}}]})
    assert await reader.count(name, tax) == 1
    assert await reader.count("rf_" + uuid4().hex, PayloadFilter()) == 0


async def test_facet_tags(reader: QdrantReader, seeded: Seed) -> None:
    name, _, _ = seeded
    assert await reader.facet(name, "tags") == FacetResponse(
        key="tags",
        values=[FacetValue(value="hr", count=2), FacetValue(value="tax", count=1)],
    )


async def test_get_point_existing_and_unknown(reader: QdrantReader, seeded: Seed) -> None:
    name, point_ids, payloads = seeded
    point = await reader.get_point(name, point_ids[0])
    assert point.id == point_ids[0]
    assert point.payload == payloads[0]
    unknown = uuid4().hex
    with pytest.raises(AppError) as excinfo:
        await reader.get_point(name, unknown)
    assert excinfo.value.code == "POINT_NOT_FOUND"
