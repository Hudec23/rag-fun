"""Maintenance jobs (rag_worker.jobs.maintenance.drop_collection, delete_points): utility jobs
without callbacks or events (contracts/jobs/drop_collection, delete_points). Real Qdrant via
qdrant-test (QDRANT_URL). The jobs are stubs — every test here is red until T-worker-040."""

import copy
import json
from collections.abc import Iterator
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pytest
from haystack import Document
from haystack.dataclasses import SparseEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from rag_worker.jobs.maintenance import delete_points, drop_collection
from rag_worker.qdrant_admin import document_store
from tests.conftest import FIXTURES
from tests.contract import errors

FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
OTHER_FILE_ID = "019a4b2c-2f00-7a3e-9c11-3b7f4e5d6a02"
DROP_PAYLOAD = json.loads((FIXTURES / "jobs__drop_collection.json").read_text())
DELETE_PAYLOAD = json.loads((FIXTURES / "jobs__delete_points.json").read_text())


def _doc(
    content: str, vector: list[float], indices: list[int], values: list[float], file_id: str
) -> Document:
    return Document(
        content=content,
        embedding=vector,
        sparse_embedding=SparseEmbedding(indices=indices, values=values),
        meta={"file_id": file_id},
    )


SEED_DOCS = [
    _doc("one", [0.1, 0.2, 0.3, 0.4], [1, 3], [0.5, 0.9], FILE_ID),
    _doc("two", [0.2, 0.4, 0.6, 0.8], [2], [0.7], FILE_ID),
    _doc("other", [0.3, 0.3, 0.5, 0.5], [0], [0.4], OTHER_FILE_ID),
]


@pytest.fixture
def qdrant(ctx: dict[str, Any]) -> Iterator[tuple[QdrantClient, str, str]]:
    """(client, fresh collection name, url) against qdrant-test; the collection is dropped in teardown."""
    url = ctx["qdrant_url"]
    client = QdrantClient(url=url)
    name = "rf_" + uuid4().hex
    yield client, name, url
    with suppress(Exception):
        client.delete_collection(name)
    client.close()


def _seed(url: str, name: str) -> int:
    """Create the collection (4 dims) and write SEED_DOCS; return the number of points written."""
    store = document_store(url, name, 4)
    written = store.write_documents(SEED_DOCS)
    assert written == len(SEED_DOCS)
    return written


def _count_file(client: QdrantClient, name: str, file_id: str) -> int:
    return client.count(
        name,
        count_filter=rest.Filter(
            must=[rest.FieldCondition(key="meta.file_id", match=rest.MatchValue(value=file_id))]
        ),
        exact=True,
    ).count


def _drop_payload(name: str) -> dict[str, Any]:
    payload = copy.deepcopy(DROP_PAYLOAD)
    payload["qdrant_name"] = name
    return payload


def _delete_payload(name: str, file_id: str) -> dict[str, Any]:
    payload = copy.deepcopy(DELETE_PAYLOAD)
    payload["qdrant_name"] = name
    payload["file_id"] = file_id
    return payload


async def test_delete_points_seeded_collection_deletes_only_file_points(ctx, qdrant) -> None:
    client, name, url = qdrant
    _seed(url, name)
    payload = _delete_payload(name, FILE_ID)
    assert errors(payload, "jobs/delete_points.schema.json") == []

    result = await delete_points(ctx, payload)

    assert result == {"status": "done", "deleted": 2}
    assert client.count(name).count == 1
    assert _count_file(client, name, FILE_ID) == 0
    assert _count_file(client, name, OTHER_FILE_ID) == 1
    assert ctx["api"].calls == []
    assert ctx["events"].events == []


async def test_drop_collection_removes_collection(ctx, qdrant) -> None:
    client, name, url = qdrant
    _seed(url, name)
    assert client.collection_exists(name)
    payload = _drop_payload(name)
    assert errors(payload, "jobs/drop_collection.schema.json") == []

    result = await drop_collection(ctx, payload)

    assert result == {"status": "done"}
    assert not client.collection_exists(name)
    assert ctx["api"].calls == []
    assert ctx["events"].events == []


async def test_invalid_payload_fails_without_raising(ctx, qdrant) -> None:
    client, name, url = qdrant
    _seed(url, name)
    bad_drop = _drop_payload("not_a_valid_name")
    assert errors(bad_drop, "jobs/drop_collection.schema.json") != []
    bad_delete = _delete_payload(name, "not-a-uuid")
    assert errors(bad_delete, "jobs/delete_points.schema.json") != []

    result = await drop_collection(ctx, bad_drop)
    assert result == {"status": "failed"}
    result = await delete_points(ctx, bad_delete)
    assert result == {"status": "failed"}

    assert client.count(name).count == 3
    assert _count_file(client, name, FILE_ID) == 2
    assert _count_file(client, name, OTHER_FILE_ID) == 1
    assert ctx["api"].calls == []
    assert ctx["events"].events == []


async def test_unreachable_qdrant_fails(ctx, qdrant) -> None:
    _, name, _ = qdrant
    payload = _drop_payload(name)
    assert errors(payload, "jobs/drop_collection.schema.json") == []
    ctx["qdrant_url"] = "http://127.0.0.1:1"

    result = await drop_collection(ctx, payload)

    assert result == {"status": "failed"}
    assert ctx["api"].calls == []
    assert ctx["events"].events == []
