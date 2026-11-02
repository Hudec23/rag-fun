"""retrieve pipelines + filters (services/worker/src/rag_worker/pipelines/retrieve.py): to_haystack_filters
output, and hybrid/dense/sparse retrieval over a fresh qdrant-test collection 'rf_' + uuid4().hex seeded
with three fake-embedded docs via qdrant_admin.document_store, dropped in teardown. The module is a stub
raising NotImplementedError, so every test here is red until T-worker-032 lands."""

from collections.abc import Iterator
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pytest
from haystack import Document
from qdrant_client import QdrantClient

from rag_worker.contracts_gen.shared.common_schema import (
    CollectionRef,
    DenseModelConfig,
    MatchAny,
    MatchAnyCondition,
    PayloadFilter,
    RangeBounds,
    RangeCondition,
)
from rag_worker.models.fakes import fake_dense, fake_sparse
from rag_worker.pipelines.retrieve import (
    build_retrieve_pipeline,
    run_retrieve,
    to_haystack_filters,
)
from rag_worker.qdrant_admin import document_store

COLLECTION_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
VACATION_CONTENT = "Employees get five vacation days each year"
TAX_CONTENT = "Payroll taxes are withheld from every salary"
POLICY_CONTENT = "The office opens at nine in the morning"


def _seed_doc(content: str, tags: list[str], page: int) -> Document:
    return Document(
        content=content,
        id=f"rf_seed:{page:05d}",
        embedding=fake_dense(content, 384),
        sparse_embedding=fake_sparse(content),
        meta={"tags": tags, "file_id": "f1", "page": page, "chunk_index": page},
    )


SEED_DOCS = [
    _seed_doc(VACATION_CONTENT, ["hr"], 1),
    _seed_doc(TAX_CONTENT, ["tax"], 2),
    _seed_doc(POLICY_CONTENT, ["policy"], 3),
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


def _seeded(qdrant: Iterator[tuple[QdrantClient, str, str]]) -> tuple[Any, CollectionRef]:
    """Fresh collection holding the three fake-embedded docs; returns (store, CollectionRef for it)."""
    _, name, url = qdrant
    store = document_store(url, name, 384)
    assert store.write_documents(SEED_DOCS) == 3
    return store, CollectionRef(
        id=COLLECTION_ID,
        qdrant_name=name,
        dense=DenseModelConfig(model="all-minilm", dims=384, ollama_url="http://x"),
        sparse_model="Qdrant/bm25",
    )


def test_to_haystack_filters_empty_is_none() -> None:
    assert to_haystack_filters(PayloadFilter()) is None


def test_to_haystack_filters_must_tags_any() -> None:
    f = PayloadFilter(must=[MatchAnyCondition(key="tags", match=MatchAny(any=["hr"]))])
    assert to_haystack_filters(f) == {
        "operator": "AND",
        "conditions": [{"field": "meta.tags", "operator": "in", "value": ["hr"]}],
    }


def test_to_haystack_filters_range_must_and_must_not() -> None:
    page_1_3 = RangeCondition(key="page", range=RangeBounds(gte=1, lte=3))
    bounds = [
        {"field": "meta.page", "operator": ">=", "value": 1},
        {"field": "meta.page", "operator": "<=", "value": 3},
    ]
    assert to_haystack_filters(PayloadFilter(must=[page_1_3])) == {
        "operator": "AND",
        "conditions": bounds,
    }
    assert to_haystack_filters(PayloadFilter(must_not=[page_1_3])) == {
        "operator": "NOT",
        "conditions": [{"operator": "AND", "conditions": bounds}],
    }


def test_hybrid_over_seeded_collection_returns_dense_and_sparse(
    ctx: dict[str, Any], qdrant: Iterator[tuple[QdrantClient, str, str]]
) -> None:
    store, collection = _seeded(qdrant)
    pipeline = build_retrieve_pipeline("hybrid", collection, store, 3, ctx["models"])
    results = run_retrieve(pipeline, "hybrid", ["vacation days", "payroll taxes"], None)
    assert [r["query"] for r in results] == ["vacation days", "payroll taxes"]
    for r in results:
        assert r["dense"] is not None
        assert len(r["dense"]) > 0
        assert r["sparse"] is not None
        assert len(r["sparse"]) > 0
    assert results[0]["dense"][0].content == VACATION_CONTENT


def test_filters_tags_tax_restrict_every_returned_doc(
    ctx: dict[str, Any], qdrant: Iterator[tuple[QdrantClient, str, str]]
) -> None:
    store, collection = _seeded(qdrant)
    pipeline = build_retrieve_pipeline("hybrid", collection, store, 3, ctx["models"])
    filters = to_haystack_filters(
        PayloadFilter(must=[MatchAnyCondition(key="tags", match=MatchAny(any=["tax"]))])
    )
    results = run_retrieve(pipeline, "hybrid", ["payroll taxes"], filters)
    assert results[0]["dense"] is not None
    assert [doc.content for doc in results[0]["dense"]] == [TAX_CONTENT]
    for r in results:
        for doc in list(r["dense"] or []) + list(r["sparse"] or []):
            assert doc.meta["tags"] == ["tax"]


def test_mode_dense_sparse_none_and_hybrid_component_names(
    ctx: dict[str, Any], qdrant: Iterator[tuple[QdrantClient, str, str]]
) -> None:
    store, collection = _seeded(qdrant)
    models = ctx["models"]
    dense_results = run_retrieve(
        build_retrieve_pipeline("dense", collection, store, 3, models),
        "dense",
        ["vacation days"],
        None,
    )
    assert dense_results[0]["sparse"] is None
    assert dense_results[0]["dense"] is not None
    assert len(dense_results[0]["dense"]) == 3
    sparse_results = run_retrieve(
        build_retrieve_pipeline("sparse", collection, store, 3, models),
        "sparse",
        ["vacation days"],
        None,
    )
    assert sparse_results[0]["dense"] is None
    assert sparse_results[0]["sparse"] is not None
    assert len(sparse_results[0]["sparse"]) > 0
    hybrid = build_retrieve_pipeline("hybrid", collection, store, 3, models)
    names = set(hybrid.to_dict()["components"])
    assert {"dense_retriever", "sparse_retriever"}.issubset(names)
