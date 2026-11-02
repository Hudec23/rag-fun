"""qdrant_admin (worker-owned Qdrant writes: store creation, file deletes, drops) against qdrant-test
(QDRANT_URL). Fresh collection 'rf_' + uuid4().hex per test, dropped in teardown."""

from collections.abc import Iterator
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pytest
from haystack import Document
from haystack.dataclasses import SparseEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from rag_worker.qdrant_admin import delete_file_points, document_store, drop_collection


def _doc(
    content: str, vector: list[float], indices: list[int], values: list[float], file_id: str
) -> Document:
    return Document(
        content=content,
        embedding=vector,
        sparse_embedding=SparseEmbedding(indices=indices, values=values),
        meta={"file_id": file_id},
    )


F1_DOCS = [
    _doc("first", [0.1, 0.2, 0.3, 0.4], [1, 3], [0.5, 0.9], "f1"),
    _doc("second", [0.2, 0.4, 0.6, 0.8], [2], [0.7], "f1"),
]
F2_DOC = _doc("other", [0.3, 0.3, 0.5, 0.5], [0], [0.4], "f2")


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


def _count_file(client: QdrantClient, name: str, file_id: str) -> int:
    return client.count(
        name,
        count_filter=rest.Filter(
            must=[rest.FieldCondition(key="meta.file_id", match=rest.MatchValue(value=file_id))]
        ),
        exact=True,
    ).count


def test_document_store_creates_named_vectors_and_payload_indexes(
    qdrant: Iterator[tuple[QdrantClient, str, str]],
) -> None:
    client, name, url = qdrant
    store = document_store(url, name, 4)
    assert store.write_documents(F1_DOCS) == 2
    info = client.get_collection(name)
    dense = info.config.params.vectors
    assert list(dense) == ["text-dense"]
    assert dense["text-dense"].size == 4
    assert dense["text-dense"].distance == rest.Distance.COSINE
    assert info.config.params.sparse_vectors["text-sparse"].modifier == rest.Modifier.IDF
    assert info.payload_schema["meta.file_id"].data_type == rest.PayloadSchemaType.KEYWORD


def test_delete_file_points_returns_count_and_leaves_other_files(
    qdrant: Iterator[tuple[QdrantClient, str, str]],
) -> None:
    client, name, url = qdrant
    store = document_store(url, name, 4)
    assert store.write_documents(F1_DOCS + [F2_DOC]) == 3
    assert delete_file_points(client, name, "f1") == 2
    assert client.count(name).count == 1
    assert _count_file(client, name, "f1") == 0
    assert _count_file(client, name, "f2") == 1


def test_delete_file_points_missing_collection_returns_zero(
    qdrant: Iterator[tuple[QdrantClient, str, str]],
) -> None:
    client, name, _ = qdrant
    assert delete_file_points(client, name, "f1") == 0


def test_drop_collection_removes_and_second_drop_does_not_raise(
    qdrant: Iterator[tuple[QdrantClient, str, str]],
) -> None:
    client, name, _ = qdrant
    client.create_collection(
        name, vectors_config=rest.VectorParams(size=4, distance=rest.Distance.COSINE)
    )
    drop_collection(client, name)
    assert not client.collection_exists(name)
    drop_collection(client, name)
    assert not client.collection_exists(name)
