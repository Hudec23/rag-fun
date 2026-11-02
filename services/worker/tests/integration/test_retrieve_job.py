"""retrieve job (rag_worker.jobs.retrieve.retrieve): read the transform artifact (or fall back to the
question), run the configured retrieval over the Qdrant collection and report the stage result. Real
Qdrant via qdrant-test (QDRANT_URL). The retrieve job is a stub — every test here is red until
T-worker-033 lands."""

import copy
import json
from collections.abc import Iterator
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pytest
from haystack import Document
from qdrant_client import QdrantClient

from rag_worker import keys
from rag_worker.jobs.retrieve import retrieve
from rag_worker.models.fakes import fake_dense, fake_sparse
from rag_worker.qdrant_admin import document_store
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "retrieve", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__retrieve.json").read_text())
TRANSFORM = json.loads((FIXTURES / "artifact_transform.json").read_text())
TRANSFORM_KEY = PAYLOAD["transform_artifact_key"]
TRANSFORM_QUERIES = TRANSFORM["queries"]
QUESTION = PAYLOAD["question"]
FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
BATCH_ID = "019a4b2c-1e00-7b00-8000-000000000001"
SEED_CONTENTS = [
    "Q3 revenue grew 12 percent year over year",
    "Subscription revenue trend improved in Q3",
    "Operating costs stayed flat while headcount increased",
]


def _event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "retrieve",
        "version": VERSION,
        "ts": TS,
        **extra,
    }


def _summary(queries: int, hits: int) -> dict[str, Any]:
    return {"stage": "retrieve", "queries": queries, "hits": hits}


def _meta(chunk_index: int) -> dict[str, Any]:
    page = chunk_index + 1
    return {
        "file_id": FILE_ID,
        "batch_id": BATCH_ID,
        "batch_name": "Q3 reports",
        "filename": "q3-report.pdf",
        "mime": "application/pdf",
        "tags": ["finance", "q3"],
        "page": page,
        "page_numbers": [page],
        "section_path": ["Q3 Report"],
        "element_type": "text",
        "chunk_index": chunk_index,
        "chunk_strategy": "recursive",
        "parse_strategy": "docling_layout",
        "ingest_run_id": RUN_ID,
        "dense_model": "all-minilm",
        "sparse_model": "Qdrant/bm25",
        "stored_at": TS,
    }


def _seed_doc(chunk_index: int, content: str) -> Document:
    return Document(
        content=content,
        id=keys.doc_id(FILE_ID, chunk_index),
        embedding=fake_dense(content, 384),
        sparse_embedding=fake_sparse(content),
        meta=_meta(chunk_index),
    )


SEED_DOCS = [_seed_doc(i, content) for i, content in enumerate(SEED_CONTENTS)]
SEED_DOC_IDS = [keys.doc_id(FILE_ID, i) for i in range(len(SEED_CONTENTS))]


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


def _seeded(qdrant: tuple[QdrantClient, str, str]) -> None:
    """Fresh collection holding the three fake-embedded docs."""
    _, name, url = qdrant
    store = document_store(url, name, 384)
    assert store.write_documents(SEED_DOCS) == 3


def _payload(name: str) -> dict[str, Any]:
    """Copy of PAYLOAD pointed at a fresh collection (384 dims)."""
    payload = copy.deepcopy(PAYLOAD)
    payload["collection"]["qdrant_name"] = name
    payload["collection"]["dense"]["dims"] = 384
    return payload


async def test_no_transform_single_query_and_valid_artifact(ctx, frozen_now, qdrant) -> None:
    assert errors(PAYLOAD, "jobs/retrieve.schema.json") == []
    client, name, _ = qdrant
    payload = _payload(name)
    payload["transform_artifact_key"] = None
    _seeded(qdrant)

    result = await retrieve(ctx, payload)

    assert result == {"status": "done", "summary": _summary(1, 3)}
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {(artifacts, ARTIFACT_KEY)}
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    assert artifact["mode"] == "hybrid"
    assert artifact["top_k"] == 10
    assert artifact["rrf_k"] == 60
    assert artifact["filters"] == PAYLOAD["params"]["filters"]
    assert errors(artifact, "artifacts/retrieve.schema.json") == []
    [entry] = artifact["per_query"]
    assert set(entry) == {"query", "dense", "sparse"}
    assert entry["query"] == QUESTION
    assert len(entry["dense"]) == 3
    assert {hit["doc_id"] for hit in entry["dense"]} == set(SEED_DOC_IDS)
    assert entry["sparse"] is not None
    assert len(entry["sparse"]) > 0
    fused = artifact["fused"]
    assert len(fused) == 3
    assert {f["hit"]["doc_id"] for f in fused} == set(SEED_DOC_IDS)
    assert client.collection_exists(name)
    assert client.count(name).count == 3
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": _summary(1, 3),
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (RUN_ID, _event("stage.completed", artifact_key=ARTIFACT_KEY, summary=_summary(1, 3))),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_transform_artifact_produces_three_queries_and_deduped_fused(
    ctx, frozen_now, qdrant
) -> None:
    client, name, _ = qdrant
    payload = _payload(name)
    artifacts = ctx["settings"].s3_bucket_artifacts
    ctx["store"].objects[(artifacts, TRANSFORM_KEY)] = (
        FIXTURES / "artifact_transform.json"
    ).read_bytes()
    _seeded(qdrant)

    result = await retrieve(ctx, payload)

    assert set(ctx["store"].objects) == {(artifacts, TRANSFORM_KEY), (artifacts, ARTIFACT_KEY)}
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    per_query = artifact["per_query"]
    assert len(per_query) == 3
    assert [entry["query"] for entry in per_query] == TRANSFORM_QUERIES
    for entry in per_query:
        assert len(entry["dense"]) == 3
        assert entry["sparse"] is not None
        assert len(entry["sparse"]) > 0
    fused = artifact["fused"]
    doc_ids = [f["hit"]["doc_id"] for f in fused]
    assert len(doc_ids) == len(set(doc_ids))
    assert set(doc_ids) == set(SEED_DOC_IDS)
    assert result == {"status": "done", "summary": _summary(3, len(doc_ids))}
    assert errors(artifact, "artifacts/retrieve.schema.json") == []
    assert client.count(name).count == 3
    assert ctx["running"] == 0


async def test_fused_ranks_source_ranks_and_summary(ctx, frozen_now, qdrant) -> None:
    client, name, _ = qdrant
    payload = _payload(name)
    payload["transform_artifact_key"] = None
    _seeded(qdrant)

    result = await retrieve(ctx, payload)

    artifacts = ctx["settings"].s3_bucket_artifacts
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    fused = artifact["fused"]
    assert len(fused) == 3
    assert [f["hit"]["rank"] for f in fused] == [1, 2, 3]
    assert {f["hit"]["doc_id"] for f in fused} == set(SEED_DOC_IDS)
    per_query = artifact["per_query"]
    for fused_hit in fused:
        assert fused_hit["source_ranks"]
        for src in fused_hit["source_ranks"]:
            source_hit = per_query[src["query_index"]][src["list"]][src["rank"] - 1]
            assert source_hit["doc_id"] == fused_hit["hit"]["doc_id"]
    assert result == {"status": "done", "summary": _summary(1, len(fused))}
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/RetrieveSummary") == []
    assert client.count(name).count == 3
    assert ctx["running"] == 0


async def test_mode_dense_fused_is_reranked_dense_and_sparse_none(ctx, frozen_now, qdrant) -> None:
    client, name, _ = qdrant
    payload = _payload(name)
    payload["transform_artifact_key"] = None
    payload["params"]["mode"] = "dense"
    _seeded(qdrant)

    result = await retrieve(ctx, payload)

    artifacts = ctx["settings"].s3_bucket_artifacts
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    assert artifact["mode"] == "dense"
    [entry] = artifact["per_query"]
    assert entry["query"] == QUESTION
    assert entry["sparse"] is None
    dense = entry["dense"]
    assert len(dense) == 3
    fused = artifact["fused"]
    assert len(fused) == len(dense)
    for i, (fused_hit, hit) in enumerate(zip(fused, dense, strict=True), start=1):
        assert fused_hit["hit"] == hit
        assert fused_hit["source_ranks"] == [{"query_index": 0, "list": "dense", "rank": i}]
    assert result == {"status": "done", "summary": _summary(1, len(fused))}
    assert errors(artifact, "artifacts/retrieve.schema.json") == []
    assert client.count(name).count == 3
    assert ctx["running"] == 0


async def test_empty_collection_done_with_empty_lists(ctx, frozen_now, qdrant) -> None:
    client, name, _ = qdrant
    payload = _payload(name)
    payload["transform_artifact_key"] = None
    payload["params"]["filters"] = {}

    result = await retrieve(ctx, payload)

    assert result == {"status": "done", "summary": _summary(1, 0)}
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {(artifacts, ARTIFACT_KEY)}
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    [entry] = artifact["per_query"]
    assert entry["query"] == QUESTION
    assert entry["dense"] == []
    assert entry["sparse"] == []
    assert artifact["fused"] == []
    assert errors(artifact, "artifacts/retrieve.schema.json") == []
    assert client.collection_exists(name)
    assert client.count(name).count == 0
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": _summary(1, 0),
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (RUN_ID, _event("stage.completed", artifact_key=ARTIFACT_KEY, summary=_summary(1, 0))),
    ]
    assert ctx["running"] == 0
