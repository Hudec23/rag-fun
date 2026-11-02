"""Unit tests for the store pipeline (services/worker/src/rag_worker/pipelines/store.py):
documents_for_store maps chunk+embed artifacts onto Haystack Documents with qdrant payload Meta
(contracts/qdrant/payload.schema.json), and build_store_pipeline wires the 'writer' DocumentWriter
with OVERWRITE. The module is a stub raising NotImplementedError, so every test here is red until
T-worker-026 lands."""

import copy
import json
from typing import Any

import pytest
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from rag_worker.errors import WorkerError
from rag_worker.pipelines.store import build_store_pipeline, documents_for_store
from tests.conftest import FIXTURES
from tests.contract import errors

FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
META_BASE: dict[str, Any] = {
    "file_id": FILE_ID,
    "batch_id": "019a4b2c-1e00-7b00-8000-000000000001",
    "batch_name": "Q3 reports",
    "filename": "q3-report.pdf",
    "mime": "application/pdf",
    "tags": ["finance", "q3"],
    "ingest_run_id": "019a4b2c-2000-7c00-9000-000000000002",
    "dense_model": "all-minilm",
    "sparse_model": "Qdrant/bm25",
    "parse_strategy": "docling_layout",
    "chunk_strategy": "recursive",
}
STORED_AT = "2026-11-01T18:22:05.123Z"


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


def _documents() -> list[Document]:
    return documents_for_store(
        _load("artifact_chunk.json"), _load("artifact_embed.json"), META_BASE, STORED_AT
    )


def test_documents_for_store_maps_artifacts_to_documents() -> None:
    chunk = _load("artifact_chunk.json")
    embed = _load("artifact_embed.json")
    docs = _documents()
    assert [doc.id for doc in docs] == [c["doc_id"] for c in chunk["chunks"]]
    assert len(docs) == 4
    for doc, c, e in zip(docs, chunk["chunks"], embed["chunks"], strict=True):
        assert doc.content == c["text"]
        assert doc.embedding == e["dense"]
        assert doc.sparse_embedding is not None
        assert doc.sparse_embedding.indices == e["sparse"]["indices"]
        assert doc.sparse_embedding.values == e["sparse"]["values"]
        meta = doc.meta
        assert meta["file_id"] == FILE_ID
        assert meta["chunk_index"] == c["index"]
        assert meta["page_numbers"] == c["page_numbers"]
        assert meta["section_path"] == c["section_path"]
        assert meta["element_type"] == c["element_type"]
        assert meta["stored_at"] == STORED_AT
        assert errors(meta, "qdrant/payload.schema.json#/$defs/Meta") == []


def test_meta_page_is_first_page_number_or_none() -> None:
    chunk = _load("artifact_chunk.json")
    embed = _load("artifact_embed.json")
    docs = documents_for_store(chunk, embed, META_BASE, STORED_AT)
    assert [doc.meta["page"] for doc in docs] == [1, 1, 1, 2]

    chunk_no_pages = copy.deepcopy(chunk)
    chunk_no_pages["chunks"][2]["page_numbers"] = []
    docs = documents_for_store(chunk_no_pages, embed, META_BASE, STORED_AT)
    assert [doc.meta["page"] for doc in docs] == [1, 1, None, 2]
    for doc in docs:
        assert errors(doc.meta, "qdrant/payload.schema.json#/$defs/Meta") == []


def test_chunk_embed_index_mismatch_raises_validation_error() -> None:
    chunk = _load("artifact_chunk.json")
    embed = _load("artifact_embed.json")
    embed_short = copy.deepcopy(embed)
    embed_short["chunks"] = embed_short["chunks"][:3]
    with pytest.raises(WorkerError) as exc_info:
        documents_for_store(chunk, embed_short, META_BASE, STORED_AT)
    assert exc_info.value.code == "VALIDATION_ERROR"
    assert exc_info.value.details == {"reason": "chunk/embed mismatch"}


def test_build_store_pipeline_writes_documents_with_overwrite() -> None:
    store = InMemoryDocumentStore()
    pipeline = build_store_pipeline(store)
    pipeline.run({"writer": {"documents": _documents()}})
    assert store.count_documents() == 4
    pipeline.run({"writer": {"documents": _documents()}})
    assert store.count_documents() == 4
